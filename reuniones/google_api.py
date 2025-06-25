from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import GoogleToken, ParticipanteReunion, Reunion
from datetime import timedelta
import uuid
import logging
import datetime
import pytz


# Configurar logging
logger = logging.getLogger(__name__)

def normalize_datetime_for_comparison(date1, date2):
    """
    Normaliza dos fechas para que ambas tengan zona horaria antes de compararlas.
    Si alguna no tiene zona horaria, se le asigna la zona horaria del servidor.
    """
    # Si alguna fecha es None, no hay nada que normalizar
    if date1 is None or date2 is None:
        return date1, date2
        
    # Convertir la primera fecha si es necesario
    if date1.tzinfo is None:
        timezone = pytz.timezone(settings.TIME_ZONE)
        date1 = timezone.localize(date1)
        
    # Convertir la segunda fecha si es necesario
    if date2.tzinfo is None:
        timezone = pytz.timezone(settings.TIME_ZONE)
        date2 = timezone.localize(date2)
        
    return date1, date2

def ensure_timezone_aware(date_obj):
    """
    Asegura que un objeto datetime tenga zona horaria.
    
    Args:
        date_obj: Objeto datetime que puede o no tener zona horaria.
        
    Returns:
        Objeto datetime con zona horaria.
    """
    if date_obj is None:
        return None
        
    if date_obj.tzinfo is None:
        timezone_obj = pytz.timezone(settings.TIME_ZONE)
        return timezone_obj.localize(date_obj)
    return date_obj

def get_valid_credentials(usuario):
    """
    Obtiene credenciales válidas para un usuario, refrescando el token si es necesario.
    """
    try:
        token = GoogleToken.objects.get(user=usuario)
    except GoogleToken.DoesNotExist:
        raise ValidationError("No se encontró un token de Google para este usuario. Por favor, conecte su cuenta de Google primero.")
    
    # Verificar scopes necesarios
    required_scopes = ['https://www.googleapis.com/auth/calendar.events']
    token_scopes = token.scopes.split()
    if not all(scope in token_scopes for scope in required_scopes):
        raise ValidationError("El token de Google no tiene los permisos necesarios para manejar eventos. Por favor, reconecte su cuenta con los permisos adecuados.")
    
    # Asegurarse de que la fecha de expiración tenga zona horaria
    expiry = ensure_timezone_aware(token.expiry)
    
    # Crear credenciales con la expiración corregida
    creds = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri=token.token_uri,
        client_id=token.client_id,
        client_secret=token.client_secret,
        scopes=token_scopes,
        expiry=expiry  # Usar la fecha con zona horaria
    )
    
    # SOLUCIÓN AQUÍ: Siempre refrescar el token para evitar problemas de comparación
    if creds.refresh_token:
        try:
            creds.refresh(Request())
            # Actualizar token en la base de datos
            token.access_token = creds.token
            token.expiry = ensure_timezone_aware(creds.expiry)  # Asegurar que la fecha tiene zona horaria
            token.save(update_fields=['access_token', 'expiry'])
            logger.info(f"Token de Google refrescado para el usuario {usuario.id}")
        except Exception as e:
            logger.error(f"Error al refrescar token para usuario {usuario.id}: {str(e)}")
            raise ValidationError(f"Error al refrescar el token de Google: {str(e)}")
    elif creds.expiry is None or datetime.datetime.now(pytz.UTC) >= ensure_timezone_aware(creds.expiry):
        # Token está expirado pero no se puede refrescar
        raise ValidationError("Su sesión con Google ha expirado y no puede ser renovada automáticamente. Por favor, reconecte su cuenta.")
    
    return creds

def iniciar_reunion(usuario, reunion):
    """
    Inicia una reunión existente o crea una nueva si no tiene enlace de Meet.
    """
    # Si hay un enlace manual, devolverlo directamente
    if reunion.link_meet and reunion.link_meet.strip() and not reunion.google_event_id:
        return reunion.link_meet
    
    # Si ya existe un enlace de Google Meet, devolverlo
    if reunion.link_meet and reunion.google_event_id:
        return reunion.link_meet
    
    # Si hay un ID de evento pero no hay enlace de Meet, intentar actualizarlo
    if reunion.google_event_id and not reunion.link_meet:
        try:
            # Obtener credenciales
            creds = get_valid_credentials(usuario)
            service = build('calendar', 'v3', credentials=creds)
            
            # Obtener el evento existente
            event = service.events().get(
                calendarId='primary',
                eventId=reunion.google_event_id
            ).execute()
            
            # Verificar si ya tiene enlace de Meet
            if 'hangoutLink' in event:
                reunion.link_meet = event['hangoutLink']
                reunion.save(update_fields=['link_meet'])
                return reunion.link_meet
            
            # Si no tiene enlace de Meet, crear uno nuevo
            conference_request = {
                'createRequest': {
                    'requestId': str(uuid.uuid4()),
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                }
            }
            
            # Asegurarse de que las fechas tienen zona horaria
            inicio = ensure_timezone_aware(reunion.fecha)
            fin = inicio + timedelta(minutes=reunion.duracion)
            
            # También actualizar la fecha en el modelo si se cambió
            if inicio != reunion.fecha:
                reunion.fecha = inicio
                reunion.save(update_fields=['fecha'])
            
            event['conferenceData'] = conference_request
            
            updated_event = service.events().update(
                calendarId='primary',
                eventId=reunion.google_event_id,
                body=event,
                conferenceDataVersion=1
            ).execute()
            
            if 'hangoutLink' in updated_event:
                reunion.link_meet = updated_event['hangoutLink']
                reunion.save(update_fields=['link_meet'])
                return reunion.link_meet
            else:
                raise ValidationError("No se pudo crear el enlace de Meet para el evento existente.")
        except Exception as e:
            logger.error(f"Error al obtener/actualizar enlace de Meet para reunión {reunion.id}: {str(e)}")
            # Si hay error, intentar crear un nuevo evento
    
    # Si no hay ID de evento o falló la actualización, crear un nuevo evento
    try:
        event_id, meet_link = crear_evento_oauth(usuario, reunion)
        return meet_link
    except ValidationError as e:
        logger.error(f"Error al crear evento para reunión {reunion.id}: {str(e)}")
        raise ValidationError(f"No se pudo crear o iniciar la reunión virtual: {str(e)}")

def crear_evento_oauth(usuario, reunion):
    """
    Crea un evento en Google Calendar con un enlace a Google Meet para la reunión especificada.
    """
    # Obtener credenciales válidas
    creds = get_valid_credentials(usuario)
    
    # Construir el servicio de Google Calendar
    try:
        service = build('calendar', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"Error al construir servicio Calendar para usuario {usuario.id}: {str(e)}")
        raise ValidationError(f"Error al conectar con Google Calendar: {str(e)}")

    # Obtener los participantes de la reunión
    participantes = ParticipanteReunion.objects.filter(reunion=reunion)
    
    # No lanzar error si no hay participantes, simplemente crear sin ellos
    attendees = []
    if participantes.exists():
        attendees = [{'email': p.email} for p in participantes]
        
        # Agregar al organizador si no está ya incluido
        organizador_correo = reunion.organizador.correo
        if not any(att['email'] == organizador_correo for att in attendees):
            attendees.append({'email': organizador_correo})

    # Calcular inicio y fin del evento
    # Asegurar que la fecha tenga zona horaria
    inicio = ensure_timezone_aware(reunion.fecha)
    
    # Si la fecha cambió, actualizar también en el modelo
    if inicio != reunion.fecha:
        reunion.fecha = inicio
    
    fin = inicio + timedelta(minutes=reunion.duracion)

    # Crear el evento
    titulo = reunion.match.desafio.nombreDesafio if hasattr(reunion.match, 'desafio') else "Reunión"
    organizador = reunion.organizador.nombre
    
    evento = {
        'summary': f'{titulo} – Reunión',
        'description': f'Reunión organizada por {organizador}\nMotivo: {reunion.motivo}',
        'start': {
            'dateTime': inicio.isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
        'end': {
            'dateTime': fin.isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
        'conferenceData': {
            'createRequest': {
                'requestId': str(uuid.uuid4()),
                'conferenceSolutionKey': {'type': 'hangoutsMeet'},
            }
        },
        'attendees': attendees,
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

    # Crear el evento en Google Calendar
    try:
        creado = service.events().insert(
            calendarId='primary',
            body=evento,
            conferenceDataVersion=1,
            sendUpdates='all',
        ).execute()
        
        # Guardar el ID del evento y el enlace de Meet en la reunión
        reunion.google_event_id = creado['id']
        reunion.link_meet = creado.get('hangoutLink', '')
        # Guardar también la fecha con zona horaria si se modificó
        reunion.save(update_fields=['google_event_id', 'link_meet', 'fecha'])
        
        logger.info(f"Evento creado para reunión {reunion.id}: {creado['id']}")
        return creado['id'], creado.get('hangoutLink', '')
    except Exception as e:
        logger.error(f"Error al crear evento para reunión {reunion.id}: {str(e)}")
        raise ValidationError(f"Error al crear el evento en Google Calendar: {str(e)}")

def actualizar_evento_oauth(usuario, reunion):
    """
    Actualiza un evento existente en Google Calendar para la reunión especificada.

    Args:
        usuario: Objeto usuario_base que representa al usuario autenticado.
        reunion: Objeto Reunion que se va a actualizar.

    Raises:
        ValidationError: Si hay un error al interactuar con la API de Google.
    """
    if not reunion.google_event_id:
        raise ValidationError("La reunión no tiene un ID de evento de Google asociado.")

    # Obtener credenciales válidas
    creds = get_valid_credentials(usuario)
    service = build('calendar', 'v3', credentials=creds)
    
    # Obtener el evento existente primero para no perder datos importantes
    try:
        evento_existente = service.events().get(
            calendarId='primary',
            eventId=reunion.google_event_id
        ).execute()
    except Exception as e:
        logger.error(f"Error al obtener evento existente {reunion.google_event_id}: {str(e)}")
        raise ValidationError(f"Error al obtener el evento de Google Calendar: {str(e)}")
    
    # Obtener participantes
    participantes = ParticipanteReunion.objects.filter(reunion=reunion)
    # ParticipanteReunion usa 'email', no 'correo'
    attendees = [{'email': p.email} for p in participantes] if participantes.exists() else []
    
    # Calcular inicio y fin del evento asegurando zona horaria
    inicio = ensure_timezone_aware(reunion.fecha)
    
    # Actualizar la fecha en el modelo si cambió
    if inicio != reunion.fecha:
        reunion.fecha = inicio
    
    fin = inicio + timedelta(minutes=reunion.duracion)

    # Mantener conferenceData si existe
    conference_data = evento_existente.get('conferenceData', {})
    
    # Crear el evento actualizado
    titulo = reunion.match.desafio.nombreDesafio if hasattr(reunion.match, 'desafio') else "Reunión"
    organizador = reunion.organizador.nombre  # usuario_base tiene campo 'nombre'
    
    evento = {
        'summary': f'{titulo} – Reunión',
        'description': f'Reunión organizada por {organizador}\nMotivo: {reunion.motivo}',
        'start': {
            'dateTime': inicio.isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
        'end': {
            'dateTime': fin.isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
        'conferenceData': conference_data,
        'attendees': attendees,
        'reminders': evento_existente.get('reminders', {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        }),
    }

    try:
        actualizado = service.events().update(
            calendarId='primary',
            eventId=reunion.google_event_id,
            body=evento,
            conferenceDataVersion=1 if not conference_data else 0,
            sendUpdates='all',
        ).execute()
        
        # Actualizar el enlace de Meet si está disponible
        campos_a_actualizar = ['fecha']
        if 'hangoutLink' in actualizado and actualizado['hangoutLink'] != reunion.link_meet:
            reunion.link_meet = actualizado['hangoutLink']
            campos_a_actualizar.append('link_meet')
        
        # Guardar los cambios
        reunion.save(update_fields=campos_a_actualizar)
            
        logger.info(f"Evento actualizado para reunión {reunion.id}: {reunion.google_event_id}")
    except Exception as e:
        logger.error(f"Error al actualizar evento para reunión {reunion.id}: {str(e)}")
        raise ValidationError(f"Error al actualizar el evento en Google Calendar: {str(e)}")

def eliminar_evento_oauth(usuario, reunion):
    """
    Elimina un evento de Google Calendar asociado a la reunión especificada.

    Args:
        usuario: Objeto usuario_base que representa al usuario autenticado.
        reunion: Objeto Reunion cuyo evento se eliminará.

    Raises:
        ValidationError: Si hay un error al interactuar con la API de Google.
    """
    if not reunion.google_event_id:
        # Si no hay ID de evento, simplemente limpiar el enlace de Meet
        if reunion.link_meet:
            reunion.link_meet = ""
            reunion.save(update_fields=['link_meet'])
        return

    # Obtener credenciales válidas
    try:
        creds = get_valid_credentials(usuario)
        service = build('calendar', 'v3', credentials=creds)

        service.events().delete(
            calendarId='primary',
            eventId=reunion.google_event_id,
            sendUpdates='all',
        ).execute()
        
        # Limpiar los campos relacionados con Google en la reunión
        reunion.google_event_id = ""
        reunion.link_meet = ""
        reunion.save(update_fields=['google_event_id', 'link_meet'])
        
        logger.info(f"Evento eliminado para reunión {reunion.id}")
    except Exception as e:
        logger.error(f"Error al eliminar evento para reunión {reunion.id}: {str(e)}")
        raise ValidationError(f"Error al eliminar el evento de Google Calendar: {str(e)}")