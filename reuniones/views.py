from datetime import datetime, timedelta

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
from .google_api import crear_evento_oauth
from .models import GoogleToken, ParticipanteReunion, Reunion, SolicitudReunion
from administracion.models import Match, usuario_base


## ----------------------------
## Vistas para Ejecutivos
## ----------------------------

@login_required
def listar_matches_ejecutivo(request):
    """Lista de matches disponibles para agendar reuniones"""
    if getattr(request.user, "rol", "") != 'ejecutivo':
        raise PermissionDenied
    
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
    if getattr(request.user, "rol", "") != 'ejecutivo':
        raise PermissionDenied
    
    match = get_object_or_404(Match, id=match_id, ejecutivo=request.user)
    contacto = getattr(match.desafio, "contacto", None)

    if request.method == 'POST':
        form = ReunionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Crear la reunión
                reunion = form.save(commit=False)
                reunion.match = match
                reunion.organizador = request.user
                reunion.fecha = form.cleaned_data['fecha']
                reunion.save()
                
                participantes = [
                    (match.ejecutivo, False),  # Ejecutivo como usuario registrado
                ]
                
                # Agregar contacto del desafío
                # Adaptado: ahora contacto es usuario_base, puede ser None
                if contacto and isinstance(contacto, usuario_base):
                    participantes.append((contacto, False))
                elif contacto and getattr(contacto, "correo", None):
                    participantes.append((None, True, contacto.correo))

                # Agregar invitados adicionales
                if form.cleaned_data.get('invitados_adicionales'):
                    for email in form.cleaned_data['invitados_adicionales'].split(','):
                        email = email.strip()
                        if email:
                            participantes.append((None, True, email))
                
                # Crear registros de participantes
                for p in participantes:
                    if p[0]:  # Usuario registrado
                        ParticipanteReunion.objects.create(
                            reunion=reunion,
                            usuario=p[0],
                            email=getattr(p[0], "email", ""),
                            nombre=getattr(p[0], "get_full_name", lambda: str(p[0]))(),
                            es_invitado_externo=p[1]
                        )
                    else:  # Invitado externo
                        ParticipanteReunion.objects.create(
                            reunion=reunion,
                            email=p[2],
                            es_invitado_externo=True
                        )
                
                # Integración con Google Calendar si está configurado
                if hasattr(request.user, 'googletoken'):
                    try:
                        event_id, meet_link = crear_evento_oauth(request.user, reunion)
                        reunion.google_event_id = event_id
                        reunion.link_meet = meet_link
                        reunion.save()
                    except Exception as e:
                        messages.warning(request, f"Reunión creada pero no se pudo conectar con Google Calendar: {str(e)}")
                
                messages.success(request, "Reunión creada exitosamente")
                return redirect('reuniones:detalle_reunion', reunion_id=reunion.id)
    else:
        form = ReunionForm(initial={
            'fecha': datetime.now() + timedelta(days=1),
            'duracion': 30,
            'tipo': 'inicial'
        })
    
    return render(request, 'reuniones/ejecutivo/crear_reunion_directa.html', {
        'form': form,
        'match': match,
        'google_conectado': hasattr(request.user, 'googletoken')
    })

@login_required
def listar_solicitudes_ejecutivo(request):
    """Solicitudes pendientes que ha recibido el ejecutivo"""
    if getattr(request.user, "rol", "") != 'ejecutivo':
        raise PermissionDenied
    
    solicitudes = SolicitudReunion.objects.filter(
        destinatario=request.user,
        estado='pendiente'
    ).select_related('match', 'solicitante', 'match__desafio')
    
    return render(request, 'reuniones/ejecutivo/listar_solicitudes_ejecutivo.html', {
        "active_page": "listar_solicitudes_ejecutivo",
        'solicitudes': solicitudes
    })

@login_required
def responder_solicitud(request, solicitud_id):
    """Vista para aceptar/rechazar una solicitud de reunión"""
    if getattr(request.user, "rol", "") != 'ejecutivo':
        raise PermissionDenied
    
    solicitud = get_object_or_404(
        SolicitudReunion, 
        id=solicitud_id, 
        destinatario=request.user,
        estado='pendiente'
    )
    contacto = getattr(solicitud.match.desafio, "contacto", None)

    if request.method == 'POST':
        form = ResponderSolicitudForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                if form.cleaned_data['accion'] == 'aceptar':
                    # Crear la reunión
                    reunion = Reunion.objects.create(
                        match=solicitud.match,
                        organizador=request.user,
                        solicitud_origen=solicitud,
                        tipo=solicitud.tipo,
                        fecha=form.cleaned_data['fecha'],
                        duracion=form.cleaned_data['duracion'],
                        motivo=solicitud.motivo
                    )
                    
                    participantes = [
                        (solicitud.match.ejecutivo, False),
                    ]
                    
                    if contacto and isinstance(contacto, usuario_base):
                        participantes.append((contacto, False))
                    elif contacto and getattr(contacto, "correo", None):
                        participantes.append((None, True, contacto.correo))
                    
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
                                email=getattr(p[0], "email", ""),
                                nombre=getattr(p[0], "get_full_name", lambda: str(p[0]))(),
                                es_invitado_externo=p[1]
                            )
                        else:
                            ParticipanteReunion.objects.create(
                                reunion=reunion,
                                email=p[2],
                                es_invitado_externo=True
                            )
                    
                    # Integración con Google Calendar
                    if hasattr(request.user, 'googletoken'):
                        try:
                            event_id, meet_link = crear_evento_oauth(request.user, reunion)
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
        'solicitud': solicitud
    })

@login_required
def listar_reuniones_ejecutivo(request):
    """Reuniones agendadas por el ejecutivo"""
    if getattr(request.user, "rol", "") != 'ejecutivo':
        raise PermissionDenied
    
    form = FiltroReunionesForm(request.GET or None)
    reuniones = Reunion.objects.filter(
        organizador=request.user
    ).select_related('match', 'match__desafio').order_by('-fecha')
    
    if form.is_valid():
        if form.cleaned_data['tipo']:
            reuniones = reuniones.filter(tipo=form.cleaned_data['tipo'])
        if form.cleaned_data['desde']:
            reuniones = reuniones.filter(fecha__gte=form.cleaned_data['desde'])
        if form.cleaned_data['hasta']:
            reuniones = reuniones.filter(fecha__lte=form.cleaned_data['hasta'])
    
    return render(request, 'reuniones/ejecutivo/listar_reuniones_ejecutivo.html', {
        "active_page": "listar_reuniones_ejecutivo",
        'reuniones': reuniones,
        'form': form
    })

@login_required
def editar_reunion(request, reunion_id):
    """Editar una reunión existente"""
    reunion = get_object_or_404(Reunion, id=reunion_id)
    if request.user != reunion.organizador:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = ReunionForm(request.POST, instance=reunion)
        if form.is_valid():
            reunion = form.save()
            if hasattr(request.user, 'googletoken') and reunion.google_event_id:
                try:
                    from .google_api import actualizar_evento_oauth
                    actualizar_evento_oauth(request.user, reunion)
                except Exception as e:
                    messages.warning(request, f"No se pudo actualizar en Google Calendar: {str(e)}")
            messages.success(request, "Reunión actualizada correctamente")
            return redirect('reuniones:detalle_reunion', reunion_id=reunion.id)
    else:
        form = ReunionForm(instance=reunion)
    return render(request, 'reuniones/ejecutivo/editar_reunion.html', {
        'form': form,
        'reunion': reunion
    })

@login_required
def eliminar_reunion(request, reunion_id):
    """Eliminar una reunión"""
    reunion = get_object_or_404(Reunion, id=reunion_id)
    if request.user != reunion.organizador:
        raise PermissionDenied
    
    if request.method == 'POST':
        if hasattr(request.user, 'googletoken') and reunion.google_event_id:
            try:
                from .google_api import eliminar_evento_oauth
                eliminar_evento_oauth(request.user, reunion)
            except Exception as e:
                messages.warning(request, f"No se pudo eliminar de Google Calendar: {str(e)}")
        reunion.delete()
        messages.success(request, "Reunión eliminada correctamente")
        return redirect('reuniones:listar_reuniones_ejecutivo')
    return render(request, 'reuniones/ejecutivo/confirmar_eliminacion.html', {
        'reunion': reunion
    })


# ----------------------------
# DETALLE DE REUNION (ambos roles)
# ----------------------------

@login_required
def detalle_reunion(request, reunion_id):
    reunion = get_object_or_404(Reunion, id=reunion_id)
    participantes = reunion.participantes.all().order_by('-es_invitado_externo', 'nombre')
    es_organizador = request.user == reunion.organizador
    google_conectado = hasattr(request.user, 'googletoken')
    return render(request, 'reuniones/detalle_reunion.html', {
        'reunion': reunion,
        'participantes': participantes,
        'es_organizador': es_organizador,
        'google_conectado': google_conectado
    })

## ----------------------------
## Vistas para Contactos
## ----------------------------

@login_required
def listar_matches_contacto(request):
    """Listar matches donde el usuario es contacto"""
    if getattr(request.user, "rol", "") != 'contacto':
        raise PermissionDenied
    matches = Match.objects.filter(
        desafio__contacto=request.user,
        isActive=True
    ).select_related('desafio', 'iniciativa')
    return render(request, 'reuniones/contacto/listar_matches.html', {
        "active_page": "listar_matches",
        'matches': matches
    })


@login_required
def solicitar_reunion_contacto(request, match_id):
    """Contacto solicita una reunión"""
    if getattr(request.user, "rol", "") != 'contacto':
        raise PermissionDenied
    match = get_object_or_404(Match, id=match_id, desafio__contacto=request.user)
    if request.method == 'POST':
        form = SolicitudReunionForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.match = match
            solicitud.solicitante = request.user
            solicitud.destinatario = match.ejecutivo
            solicitud.save()
            messages.success(request, "Solicitud enviada correctamente.")
            return redirect('reuniones:listar_solicitudes_contacto')
    else:
        form = SolicitudReunionForm()
    return render(request, 'reuniones/contacto/solicitar_reunion.html', {'form': form, 'match': match})

@login_required
def listar_solicitudes_contacto(request):
    """Listar solicitudes enviadas por el contacto"""
    if getattr(request.user, "rol", "") != 'contacto':
        raise PermissionDenied
    solicitudes = SolicitudReunion.objects.filter(
        solicitante=request.user
    ).select_related('match', 'destinatario').order_by('-creada_en')
    return render(request, 'reuniones/contacto/listar_solicitudes.html', {
        "active_page": "listar_solicitudes",
        'solicitudes': solicitudes
    })

@login_required
def listar_reuniones_contacto(request):
    """Reuniones donde el contacto es participante"""
    # Ahora el rol va en usuario_base
    if getattr(request.user, "rol", "") != 'contacto':
        raise PermissionDenied
    
    es_contacto = Match.objects.filter(desafio__contacto=request.user).exists()
    if not es_contacto:
        return HttpResponse("No estás vinculado como contacto en ningún desafío.", status=400)

    form = FiltroReunionesForm(request.GET or None)
    reuniones = Reunion.objects.filter(
        match__desafio__contacto=request.user
    ).select_related('match', 'organizador', 'match__desafio').order_by('-fecha')

    if form.is_valid():
        if form.cleaned_data['tipo']:
            reuniones = reuniones.filter(tipo=form.cleaned_data['tipo'])
        if form.cleaned_data['desde']:
            reuniones = reuniones.filter(fecha__gte=form.cleaned_data['desde'])
        if form.cleaned_data['hasta']:
            reuniones = reuniones.filter(fecha__lte=form.cleaned_data['hasta'])

    return render(request, 'reuniones/contacto/listar_reuniones.html', {
        "active_page": "listar_reuniones",
        'reuniones': reuniones,
        'form': form
    })


## ----------------------------
## Vistas para Google OAuth
## ----------------------------

@login_required
def google_oauth_init(request):
    """Inicia el flujo de OAuth con Google"""
    from google_auth_oauthlib.flow import Flow
    from django.conf import settings
    import os
    
    # Configuración para desarrollo (permite HTTP)
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_CLIENT_SECRETS_FILE,
        scopes=settings.GOOGLE_OAUTH_SCOPES,
        redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI
    )
    
    # Guardamos el next_url en el state para redirigir después
    next_url = request.GET.get('next', '/')
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=next_url
    )
    
    request.session['google_oauth_state'] = state
    return redirect(authorization_url)

@login_required
def google_oauth_callback(request):
    """Callback para completar el flujo de OAuth"""
    from google_auth_oauthlib.flow import Flow
    from django.conf import settings
    from django.urls import reverse
    import os
    
    # Configuración para desarrollo
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    state = request.session.pop('google_oauth_state', '')
    next_url = request.GET.get('state', reverse('reuniones:home'))
    
    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_CLIENT_SECRETS_FILE,
        scopes=settings.GOOGLE_OAUTH_SCOPES,
        redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI,
        state=state
    )
    
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    
    creds = flow.credentials
    
    # Guardar o actualizar el token
    GoogleToken.objects.update_or_create(
        user=request.user,
        defaults={
            'access_token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': ' '.join(creds.scopes),
            'expiry': creds.expiry
        }
    )
    
    messages.success(request, "Cuenta de Google conectada exitosamente")
    return redirect(next_url)

@login_required
def google_disconnect(request):
    """Desconectar la cuenta de Google"""
    if hasattr(request.user, 'googletoken'):
        request.user.googletoken.delete()
        messages.success(request, "Cuenta de Google desconectada")
    return redirect(request.META.get('HTTP_REFERER', 'reuniones:listar_reuniones_ejecutivo'))