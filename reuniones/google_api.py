from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import GoogleToken, ParticipanteReunion
from datetime import timedelta
import uuid

def crear_evento_oauth(user, reunion):
    """
    Crea un evento en Google Calendar con un enlace a Google Meet para la reunión especificada.

    Args:
        user: Objeto CustomUser que representa al usuario autenticado.
        reunion: Objeto Reunion para la cual se creará el evento.

    Returns:
        tuple: (event_id, meet_link) con el ID del evento y el enlace de Google Meet.

    Raises:
        ValidationError: Si no hay un token de Google válido, los scopes son insuficientes,
                        o hay un error al interactuar con la API de Google.
    """
    # Validar que el usuario tenga un token de Google
    try:
        token = GoogleToken.objects.get(user=user)
    except GoogleToken.DoesNotExist:
        raise ValidationError("No se encontró un token de Google para este usuario.")

    # Verificar que los scopes necesarios estén presentes
    required_scopes = ['https://www.googleapis.com/auth/calendar.events']
    token_scopes = token.scopes.split()
    if not all(scope in token_scopes for scope in required_scopes):
        raise ValidationError("El token de Google no tiene los permisos necesarios para crear eventos.")

    # Crear credenciales
    creds = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri=token.token_uri,
        client_id=token.client_id,
        client_secret=token.client_secret,
        scopes=token_scopes,
    )

    # Refrescar el token si está expirado
    if not creds.valid and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token.access_token = creds.token
            token.expiry = creds.expiry
            token.save(update_fields=['access_token', 'expiry'])
        except Exception as e:
            raise ValidationError(f"Error al refrescar el token de Google: {str(e)}")

    # Construir el servicio de Google Calendar
    try:
        service = build('calendar', 'v3', credentials=creds)
    except Exception as e:
        raise ValidationError(f"Error al conectar con Google Calendar: {str(e)}")

    # Obtener los participantes de la reunión
    participantes = ParticipanteReunion.objects.filter(reunion=reunion)
    if not participantes.exists():
        raise ValidationError("No hay participantes asociados a la reunión.")

    # Calcular inicio y fin del evento
    inicio = reunion.fecha
    fin = inicio + timedelta(minutes=reunion.duracion)

    # Crear el evento
    evento = {
        'summary': f'{reunion.match.desafio.nombreDesafio} – Reunión',
        'description': f'Reunión organizada por {reunion.organizador.get_full_name()}\nMotivo: {reunion.motivo}',
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
        'attendees': [{'email': p.email} for p in participantes],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},  # Recordatorio 1 día antes
                {'method': 'popup', 'minutes': 10},       # Recordatorio 10 minutos antes
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
    except Exception as e:
        raise ValidationError(f"Error al crear el evento en Google Calendar: {str(e)}")

    return creado['id'], creado.get('hangoutLink')

def actualizar_evento_oauth(user, reunion):
    """
    Actualiza un evento existente en Google Calendar para la reunión especificada.

    Args:
        user: Objeto CustomUser que representa al usuario autenticado.
        reunion: Objeto Reunion que se va a actualizar.

    Raises:
        ValidationError: Si no hay un token de Google válido, los scopes son insuficientes,
                        o hay un error al interactuar con la API de Google.
    """
    if not reunion.google_event_id:
        raise ValidationError("La reunión no tiene un ID de evento de Google asociado.")

    try:
        token = GoogleToken.objects.get(user=user)
    except GoogleToken.DoesNotExist:
        raise ValidationError("No se encontró un token de Google para este usuario.")

    required_scopes = ['https://www.googleapis.com/auth/calendar.events']
    token_scopes = token.scopes.split()
    if not all(scope in token_scopes for scope in required_scopes):
        raise ValidationError("El token de Google no tiene los permisos necesarios para actualizar eventos.")

    creds = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri=token.token_uri,
        client_id=token.client_id,
        client_secret=token.client_secret,
        scopes=token_scopes,
    )

    if not creds.valid and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token.access_token = creds.token
            token.expiry = creds.expiry
            token.save(update_fields=['access_token', 'expiry'])
        except Exception as e:
            raise ValidationError(f"Error al refrescar el token de Google: {str(e)}")

    service = build('calendar', 'v3', credentials=creds)
    participantes = ParticipanteReunion.objects.filter(reunion=reunion)
    inicio = reunion.fecha
    fin = inicio + timedelta(minutes=reunion.duracion)

    evento = {
        'summary': f'{reunion.match.desafio.nombreDesafio} – Reunión',
        'description': f'Reunión organizada por {reunion.organizador.get_full_name()}\nMotivo: {reunion.motivo}',
        'start': {
            'dateTime': inicio.isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
        'end': {
            'dateTime': fin.isoformat(),
            'timeZone': settings.TIME_ZONE,
        },
        'attendees': [{'email': p.email} for p in participantes],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

    try:
        service.events().update(
            calendarId='primary',
            eventId=reunion.google_event_id,
            body=evento,
            sendUpdates='all',
        ).execute()
    except Exception as e:
        raise ValidationError(f"Error al actualizar el evento en Google Calendar: {str(e)}")

def eliminar_evento_oauth(user, reunion):
    """
    Elimina un evento de Google Calendar asociado a la reunión especificada.

    Args:
        user: Objeto CustomUser que representa al usuario autenticado.
        reunion: Objeto Reunion cuyo evento se eliminará.

    Raises:
        ValidationError: Si no hay un token de Google válido, los scopes son insuficientes,
                        o hay un error al interactuar con la API de Google.
    """
    if not reunion.google_event_id:
        raise ValidationError("La reunión no tiene un ID de evento de Google asociado.")

    try:
        token = GoogleToken.objects.get(user=user)
    except GoogleToken.DoesNotExist:
        raise ValidationError("No se encontró un token de Google para este usuario.")

    required_scopes = ['https://www.googleapis.com/auth/calendar.events']
    token_scopes = token.scopes.split()
    if not all(scope in token_scopes for scope in required_scopes):
        raise ValidationError("El token de Google no tiene los permisos necesarios para eliminar eventos.")

    creds = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri=token.token_uri,
        client_id=token.client_id,
        client_secret=token.client_secret,
        scopes=token_scopes,
    )

    if not creds.valid and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token.access_token = creds.token
            token.expiry = creds.expiry
            token.save(update_fields=['access_token', 'expiry'])
        except Exception as e:
            raise ValidationError(f"Error al refrescar el token de Google: {str(e)}")

    service = build('calendar', 'v3', credentials=creds)

    try:
        service.events().delete(
            calendarId='primary',
            eventId=reunion.google_event_id,
            sendUpdates='all',
        ).execute()
    except Exception as e:
        raise ValidationError(f"Error al eliminar el evento de Google Calendar: {str(e)}")