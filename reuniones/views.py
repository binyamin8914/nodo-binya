from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    FiltroReunionesForm,
    ResponderSolicitudForm,
    ReunionForm,
    SolicitudReunionForm,
)
from .models import GoogleToken, ParticipanteReunion, Reunion, SolicitudReunion
from administracion.models import Match, usuario_base
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from .google_api import iniciar_reunion
import logging
import traceback
from .utils import puede_unirse_reunion, tiempo_restante_reunion, encode_google_calendar_id

# ----------------------------
def safe_crear_evento_oauth(perfil, reunion):
    """Wrapper que asegura fechas con zona horaria antes de crear eventos"""
    # Asegurar que la fecha tenga zona horaria
    from django.utils import timezone
    import traceback
    
    try:
        if reunion.fecha and reunion.fecha.tzinfo is None:
            # Añadir zona horaria a la fecha y guardar
            reunion.fecha = timezone.make_aware(reunion.fecha)
            reunion.save(update_fields=['fecha'])
            print(f"Se añadió zona horaria a fecha de reunión {reunion.id}: {reunion.fecha}")
    except Exception as e:
        print(f"Error al preparar fecha: {str(e)}")
        print(traceback.format_exc())
    
    # Ahora llamamos a la función original
    from .google_api import crear_evento_oauth
    try:
        return crear_evento_oauth(perfil, reunion)
    except Exception as e:
        if "naive and offset-aware" in str(e):
            print("Detectado error de zona horaria, intentando forzar zona horaria...")
            try:
                # Intento final con fuerza bruta
                reunion.fecha = timezone.make_aware(reunion.fecha.replace(tzinfo=None))
                reunion.save()
                return crear_evento_oauth(perfil, reunion)
            except Exception as inner_e:
                print(f"Falló intento final: {str(inner_e)}")
                raise inner_e
        else:
            raise e

# --- FUNCIONES DE UTILIDAD ---
def get_user_perfil(user):
    try:
        return usuario_base.objects.get(correo=user.email)
    except usuario_base.DoesNotExist:
        return None

def get_user_rol(user):
    perfil = get_user_perfil(user)
    return perfil.rol if perfil else ""

# Función nueva para estandarizar la verificación de Google
def tiene_google_conectado(perfil):
    """Verifica de manera uniforme si un usuario tiene token de Google"""
    return GoogleToken.objects.filter(user=perfil).exists()


# ----------------------------
# Vistas para Ejecutivos
# ----------------------------

@login_required
def listar_matches_ejecutivo(request):
    """Lista de matches disponibles para agendar reuniones"""
    if get_user_rol(request.user) != 'ejecutivo':
        raise PermissionDenied

    # Match.ejecutivo es un User, así que puedes usar request.user directamente
    matches = Match.objects.filter(
        ejecutivo=request.user,
        isActive=True
    ).select_related('desafio', 'iniciativa')

    return render(request, 'reuniones/ejecutivo/listar_matches_ejecutivo.html', {
        "active_page": "listar_matches_ejecutivo",
        'matches': matches
    })


@login_required
def crear_reunion_directa(request, match_id):
    """Vista para que ejecutivo cree reunión sin solicitud previa"""
    if get_user_rol(request.user) != 'ejecutivo':
        raise PermissionDenied

    match = get_object_or_404(Match, id=match_id, ejecutivo=request.user)
    perfil = get_user_perfil(request.user)
    contacto = getattr(match.desafio, "contacto", None)  # contacto es usuario_base
    
    # CAMBIO AQUÍ: Usar la nueva función en lugar de hasattr
    google_conectado = tiene_google_conectado(perfil)

    if request.method == 'POST':
        form = ReunionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Crear la reunión
                reunion = form.save(commit=False)
                reunion.match = match
                reunion.organizador = perfil
                fecha = form.cleaned_data['fecha']
                if fecha.tzinfo is None:
                    fecha = timezone.make_aware(fecha)
                reunion.fecha = fecha
                
                reunion.save()

                participantes = [
                    (perfil, False),  # Ejecutivo usuario_base
                ]
                if contacto:
                    participantes.append((contacto, False))

                # Agregar invitados adicionales
                if form.cleaned_data.get('invitados_adicionales'):
                    for email in form.cleaned_data['invitados_adicionales'].split(','):
                        email = email.strip()
                        if email:
                            participantes.append((None, True, email))

                for p in participantes:
                    if p[0]:  # usuario_base
                        ParticipanteReunion.objects.create(
                            reunion=reunion,
                            usuario=p[0],
                            email=p[0].correo,
                            nombre=p[0].nombre,
                            es_invitado_externo=p[1]
                        )
                    else:  # invitado externo
                        ParticipanteReunion.objects.create(
                            reunion=reunion,
                            email=p[2],
                            es_invitado_externo=True
                        )

                # CAMBIO AQUÍ: Usar google_conectado en lugar de hasattr
                if google_conectado:
                    try:
                        event_id, meet_link = safe_crear_evento_oauth(perfil, reunion)
                        reunion.google_event_id = event_id
                        reunion.link_meet = meet_link
                        reunion.save()
                    except Exception as e:
                        messages.warning(request, f"Reunión creada pero no se pudo conectar con Google Calendar: {str(e)}")

                messages.success(request, "Reunión creada exitosamente")
                return redirect('reuniones:detalle_reunion', reunion_id=reunion.id)
    else:
        form = ReunionForm(initial={
            'fecha': timezone.now() + timedelta(days=1),
            'duracion': 30,
            'tipo': 'inicial'
        })

    return render(request, 'reuniones/ejecutivo/crear_reunion_directa.html', {
        'form': form,
        'match': match,
        'google_conectado': google_conectado  # CAMBIO AQUÍ: Usar la nueva variable
    })


@login_required
def listar_solicitudes_ejecutivo(request):
    """Solicitudes pendientes que ha recibido el ejecutivo"""
    if get_user_rol(request.user) != 'ejecutivo':
        raise PermissionDenied

    perfil = get_user_perfil(request.user)
    solicitudes = SolicitudReunion.objects.filter(
        destinatario=perfil,
        estado='pendiente'
    ).select_related('match', 'solicitante', 'match__desafio')

    return render(request, 'reuniones/ejecutivo/listar_solicitudes_ejecutivo.html', {
        "active_page": "listar_solicitudes_ejecutivo",
        'solicitudes': solicitudes
    })


@login_required
def responder_solicitud(request, solicitud_id):
    """Vista para aceptar/rechazar una solicitud de reunión"""
    if get_user_rol(request.user) != 'ejecutivo':
        raise PermissionDenied

    perfil = get_user_perfil(request.user)
    solicitud = get_object_or_404(
        SolicitudReunion,
        id=solicitud_id,
        destinatario=perfil,
        estado='pendiente'
    )
    contacto = getattr(solicitud.match.desafio, "contacto", None)
    
    # CAMBIO AQUÍ: Usar la nueva función para verificar Google
    google_conectado = tiene_google_conectado(perfil)

    if request.method == 'POST':
        form = ResponderSolicitudForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                if form.cleaned_data['accion'] == 'aceptar':
                    reunion = Reunion.objects.create(
                        match=solicitud.match,
                        organizador=perfil,
                        solicitud_origen=solicitud,
                        tipo=solicitud.tipo,
                        fecha=form.cleaned_data['fecha'],
                        duracion=form.cleaned_data['duracion'],
                        motivo=solicitud.motivo
                    )
                    participantes = [
                        (perfil, False),
                    ]
                    if contacto:
                        participantes.append((contacto, False))
                    if solicitud.invitados_adicionales:
                        for email in solicitud.invitados_adicionales.split(','):
                            email = email.strip()
                            if email:
                                participantes.append((None, True, email))
                    for p in participantes:
                        if p[0]:
                            ParticipanteReunion.objects.create(
                                reunion=reunion,
                                usuario=p[0],
                                email=p[0].correo,
                                nombre=p[0].nombre,
                                es_invitado_externo=p[1]
                            )
                        else:
                            ParticipanteReunion.objects.create(
                                reunion=reunion,
                                email=p[2],
                                es_invitado_externo=True
                            )
                    # CAMBIO AQUÍ: Usar google_conectado en lugar de hasattr
                    if google_conectado:
                        try:
                            event_id, meet_link = safe_crear_evento_oauth(perfil, reunion)
                            reunion.google_event_id = event_id
                            reunion.link_meet = meet_link
                            reunion.save()
                        except Exception as e:
                            messages.warning(request, f"Error con Google Calendar: {str(e)}")
                    solicitud.estado = 'aceptada'
                    messages.success(request, "Solicitud aceptada y reunión creada")
                else:
                    solicitud.estado = 'rechazada'
                    messages.success(request, "Solicitud rechazada")
                solicitud.save()
                return redirect('reuniones:listar_solicitudes_ejecutivo')
    else:
        form = ResponderSolicitudForm(initial={
            'fecha': solicitud.fecha_propuesta,
            'duracion': solicitud.duracion_propuesta
        })

    return render(request, 'reuniones/ejecutivo/responder_solicitud.html', {
        'form': form,
        'solicitud': solicitud,
        'google_conectado': google_conectado  # CAMBIO AQUÍ: Añadir esta variable
    })


@login_required
def listar_reuniones_ejecutivo(request):
    """Reuniones agendadas por el ejecutivo"""
    if get_user_rol(request.user) != 'ejecutivo':
        raise PermissionDenied

    perfil = get_user_perfil(request.user)
    
    # CAMBIO AQUÍ: Usar la función estandarizada
    google_conectado = tiene_google_conectado(perfil)
    
    form = FiltroReunionesForm(request.GET or None)
    reuniones = Reunion.objects.filter(
        organizador=perfil
    ).select_related('match', 'match__desafio').order_by('-fecha')

    if form.is_valid():
        if form.cleaned_data['tipo']:
            reuniones = reuniones.filter(tipo=form.cleaned_data['tipo'])
        if form.cleaned_data['desde']:
            reuniones = reuniones.filter(fecha__gte=form.cleaned_data['desde'])
        if form.cleaned_data['hasta']:
            reuniones = reuniones.filter(fecha__lte=form.cleaned_data['hasta'])

    # Añadir información de si se puede unir a cada reunión
    for reunion in reuniones:
        reunion.puede_unirse = puede_unirse_reunion(reunion)

    return render(request, 'reuniones/ejecutivo/listar_reuniones_ejecutivo.html', {
        "active_page": "listar_reuniones_ejecutivo",
        'reuniones': reuniones,
        'form': form,
        'google_conectado': google_conectado,
        'user': request.user
    })

@login_required
def editar_reunion(request, reunion_id):
    """Editar una reunión existente"""
    reunion = get_object_or_404(Reunion, id=reunion_id)
    perfil = get_user_perfil(request.user)
    if reunion.organizador != perfil:
        raise PermissionDenied
    
    # CAMBIO AQUÍ: Usar la función estandarizada
    google_conectado = tiene_google_conectado(perfil)

    if request.method == 'POST':
        form = ReunionForm(request.POST, instance=reunion)
        if form.is_valid():
            reunion = form.save()
            # CAMBIO AQUÍ: Usar google_conectado en lugar de hasattr
            if google_conectado and reunion.google_event_id:
                try:
                    from .google_api import actualizar_evento_oauth
                    actualizar_evento_oauth(perfil, reunion)
                except Exception as e:
                    messages.warning(request, f"No se pudo actualizar en Google Calendar: {str(e)}")
            messages.success(request, "Reunión actualizada correctamente")
            return redirect('reuniones:detalle_reunion', reunion_id=reunion.id)
    else:
        form = ReunionForm(instance=reunion)
    return render(request, 'reuniones/ejecutivo/editar_reunion.html', {
        'form': form,
        'reunion': reunion,
        'google_conectado': google_conectado  # CAMBIO AQUÍ: Añadir esta variable
    })


@login_required
def eliminar_reunion(request, reunion_id):
    """Eliminar una reunión"""
    reunion = get_object_or_404(Reunion, id=reunion_id)
    perfil = get_user_perfil(request.user)
    if reunion.organizador != perfil:
        raise PermissionDenied
    
    # CAMBIO AQUÍ: Usar la función estandarizada
    google_conectado = tiene_google_conectado(perfil)

    if request.method == 'POST':
        # CAMBIO AQUÍ: Usar google_conectado en lugar de hasattr
        if google_conectado and reunion.google_event_id:
            try:
                from .google_api import eliminar_evento_oauth
                eliminar_evento_oauth(perfil, reunion)
            except Exception as e:
                messages.warning(request, f"No se pudo eliminar de Google Calendar: {str(e)}")
        reunion.delete()
        messages.success(request, "Reunión eliminada correctamente")
        return redirect('reuniones:listar_reuniones_ejecutivo')
    return render(request, 'reuniones/ejecutivo/confirmar_eliminacion.html', {
        'reunion': reunion,
        'google_conectado': google_conectado  # CAMBIO AQUÍ: Añadir esta variable
    })


# ----------------------------
# DETALLE DE REUNION (ambos roles)
# ----------------------------

@login_required
def detalle_reunion(request, reunion_id):
    reunion = get_object_or_404(Reunion, id=reunion_id)
    participantes = reunion.participantes.all().order_by('-es_invitado_externo', 'nombre')
    perfil = get_user_perfil(request.user)
    es_organizador = perfil == reunion.organizador
    
    # CAMBIO AQUÍ: Usar la función estandarizada
    google_conectado = tiene_google_conectado(perfil)

    # Si es una solicitud POST para regenerar enlace
    if request.method == 'POST' and 'regenerar_enlace' in request.POST and es_organizador and google_conectado:
        try:
            event_id, meet_link = safe_crear_evento_oauth(perfil, reunion)
            reunion.google_event_id = event_id
            reunion.link_meet = meet_link
            reunion.save()
            messages.success(request, "Enlace de Meet regenerado correctamente")
        except Exception as e:
            messages.error(request, f"No se pudo regenerar el enlace: {str(e)}")
        return redirect('reuniones:detalle_reunion', reunion_id=reunion.id)

    # Verificar si ya se puede unir a la reunión
    puede_unirse = puede_unirse_reunion(reunion)
    tiempo_restante = tiempo_restante_reunion(reunion)
    
    # Codificar el ID del evento para la URL de Google Calendar
    calendar_id_encoded = None
    if reunion.google_event_id:
        calendar_id_encoded = encode_google_calendar_id(reunion.google_event_id)
        print(f"ID original: {reunion.google_event_id}")
        print(f"ID codificado: {calendar_id_encoded}")

    return render(request, 'reuniones/detalle_reunion.html', {
        'reunion': reunion,
        'participantes': participantes,
        'es_organizador': es_organizador,
        'google_conectado': google_conectado,
        'puede_unirse': puede_unirse,
        'tiempo_restante': tiempo_restante,
        'calendar_id_encoded': calendar_id_encoded
    })


# ----------------------------
# Vistas para Contactos
# ----------------------------

# @login_required
# def listar_matches_contacto(request):
#     """Listar matches donde el usuario es contacto"""
#     if get_user_rol(request.user) != 'contacto':
#         raise PermissionDenied
#
#     perfil = get_user_perfil(request.user)
#     # Match.desafio.contacto es usuario_base
#     matches = Match.objects.filter(
#         desafio__contacto=perfil,
#         isActive=True
#     ).select_related('desafio', 'iniciativa')
#     return render(request, 'reuniones/contacto/listar_matches.html', {
#         "active_page": "listar_matches",
#         'matches': matches
#     })
#
#
# @login_required
# def solicitar_reunion_contacto(request, match_id):
#     """Contacto solicita una reunión"""
#     if get_user_rol(request.user) != 'contacto':
#         raise PermissionDenied
#
#     perfil = get_user_perfil(request.user)
#     match = get_object_or_404(Match, id=match_id, desafio__contacto=perfil)
#     if request.method == 'POST':
#         form = SolicitudReunionForm(request.POST)
#         if form.is_valid():
#             solicitud = form.save(commit=False)
#             solicitud.match = match
#             solicitud.solicitante = perfil
#             # El ejecutivo destino del match, se obtiene desde Match.ejecutivo,
#             # pero SolicitudReunion.destinatario espera usuario_base. 
#             # Debes mapear el User a usuario_base por email.
#             try:
#                 ejecutivo_user = match.ejecutivo
#                 ejecutivo_base = usuario_base.objects.get(correo=ejecutivo_user.email)
#             except usuario_base.DoesNotExist:
#                 messages.error(request, "No se encontró el ejecutivo correspondiente en usuario_base.")
#                 return redirect('reuniones:listar_matches')
#             solicitud.destinatario = ejecutivo_base
#             solicitud.save()
#             messages.success(request, "Solicitud enviada correctamente.")
#             return redirect('reuniones:listar_solicitudes_contacto')
#     else:
#         form = SolicitudReunionForm()
#     return render(request, 'reuniones/contacto/solicitar_reunion.html', {'form': form, 'match': match})
#
#
# @login_required
# def listar_solicitudes_contacto(request):
#     """Listar solicitudes enviadas por el contacto"""
#     if get_user_rol(request.user) != 'contacto':
#         raise PermissionDenied
#
#     perfil = get_user_perfil(request.user)
#     solicitudes = SolicitudReunion.objects.filter(
#         solicitante=perfil
#     ).select_related('match', 'destinatario').order_by('-creada_en')
#     return render(request, 'reuniones/contacto/listar_solicitudes.html', {
#         "active_page": "listar_solicitudes",
#         'solicitudes': solicitudes
#     })
#
#
# @login_required
# def listar_reuniones_contacto(request):
#     """Reuniones donde el contacto es participante"""
#     if get_user_rol(request.user) != 'contacto':
#         raise PermissionDenied
#
#     perfil = get_user_perfil(request.user)
#     # CAMBIO AQUÍ: Usar la función estandarizada
#     google_conectado = tiene_google_conectado(perfil)
#     
#     es_contacto = Match.objects.filter(desafio__contacto=perfil).exists()
#     if not es_contacto:
#         return HttpResponse("No estás vinculado como contacto en ningún desafío.", status=400)
#
#     form = FiltroReunionesForm(request.GET or None)
#     reuniones = Reunion.objects.filter(
#         match__desafio__contacto=perfil
#     ).select_related('match', 'organizador', 'match__desafio').order_by('-fecha')
#
#     if form.is_valid():
#         if form.cleaned_data['tipo']:
#             reuniones = reuniones.filter(tipo=form.cleaned_data['tipo'])
#         if form.cleaned_data['desde']:
#             reuniones = reuniones.filter(fecha__gte=form.cleaned_data['desde'])
#         if form.cleaned_data['hasta']:
#             reuniones = reuniones.filter(fecha__lte=form.cleaned_data['hasta'])
#
#     # Añadir información de si se puede unir a cada reunión
#     for reunion in reuniones:
#         reunion.puede_unirse = puede_unirse_reunion(reunion)
#
#     return render(request, 'reuniones/contacto/listar_reuniones.html', {
#         "active_page": "listar_reuniones",
#         'reuniones': reuniones,
#         'form': form,
#         'google_conectado': google_conectado  # CAMBIO AQUÍ: Añadir esta variable
#     })


# -------------------
# Vistas para Google 
# -------------------

# Configurar logging
logger = logging.getLogger(__name__)

@login_required
def iniciar_reunion_virtual(request, reunion_id):
    """
    Vista para iniciar una reunión virtual o unirse a una existente.
    Si la reunión ya tiene un enlace de Meet, redirige a ese enlace.
    Si no tiene enlace, crea un evento en Google Calendar con enlace Meet.
    """
    try:
        # Obtener la reunión
        reunion = Reunion.objects.get(pk=reunion_id)
        
        # Obtener el usuario_base correspondiente al User actual
        try:
            usuario = usuario_base.objects.get(correo=request.user.email)
        except usuario_base.DoesNotExist:
            messages.error(request, "No se encontró un registro de usuario asociado. Contacta al administrador.")
            return redirect('reuniones:listar_reuniones_ejecutivo')
        
        # Verificar que el usuario tenga acceso a esta reunión
        es_organizador = reunion.organizador == usuario
        es_participante = ParticipanteReunion.objects.filter(
            reunion=reunion, 
            email=usuario.correo
        ).exists()
        
        if not (es_organizador or es_participante):
            messages.error(request, "No tienes permiso para acceder a esta reunión.")
            return redirect('reuniones:listar_reuniones_ejecutivo')
        
        # Verificar si existe un enlace manual (no requiere OAuth)
        if reunion.link_meet and not reunion.google_event_id:
            return redirect(reunion.link_meet)
            
        # CAMBIO AQUÍ: Usar la función estandarizada para verificar token
        if not tiene_google_conectado(usuario):
            # Si no tiene token, redirigir a la página para conectar con Google
            return render(request, 'reuniones/error_google_token.html', {'reunion_id': reunion_id})
        
        # Iniciar reunión pasando el usuario_base
        meet_link = iniciar_reunion(usuario, reunion)
        
        if meet_link:
            return redirect(meet_link)
        else:
            messages.error(request, "No se pudo obtener un enlace para la reunión virtual.")
    except Reunion.DoesNotExist:
        messages.error(request, "La reunión solicitada no existe.")
    except ValidationError as e:
        messages.error(request, str(e))
    except Exception as e:
        logger.error(f"Error en iniciar_reunion_virtual: {str(e)}\n{traceback.format_exc()}")
        messages.error(request, f"Error al iniciar la reunión: {str(e)}")
    
    return redirect('reuniones:listar_reuniones_ejecutivo')