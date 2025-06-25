import os
import json
import secrets
import logging
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from administracion.models import usuario_base
from .models import GoogleToken

# Configurar logging
logger = logging.getLogger(__name__)

# Configuración de OAuth2
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
CLIENT_CONFIG = {
    "web": {
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
        "redirect_uris": [settings.GOOGLE_OAUTH_REDIRECT_URI],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}

def credentials_to_dict(credentials):
    """Convierte credenciales en un diccionario para almacenar en sesión"""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

@login_required
def iniciar_oauth_google(request):
    """Inicia el flujo de autorización OAuth con Google"""
    try:
        # Obtenemos el usuario base correspondiente
        usuario = usuario_base.objects.get(correo=request.user.email)
        
        # Guardamos la URL de retorno después de la autenticación
        next_url = request.GET.get('next', reverse('reuniones:listar_reuniones_ejecutivo'))
        request.session['oauth_next_url'] = next_url
        
        # Generamos un estado para prevenir CSRF
        state = secrets.token_urlsafe(16)
        request.session['oauth_state'] = state
        
        # Creamos el flujo de OAuth
        flow = Flow.from_client_config(
            client_config=CLIENT_CONFIG,
            scopes=SCOPES,
            redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI
        )
        
        # Generamos la URL de autorización
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'  # Forzar la solicitud de refresh_token
        )
        
        # Guardamos la información de redirección en la sesión
        # No podemos guardar el objeto flow directamente, pero podemos guardar su configuración
        request.session['flow_client_config'] = CLIENT_CONFIG
        request.session['flow_scopes'] = SCOPES
        request.session['flow_redirect_uri'] = settings.GOOGLE_OAUTH_REDIRECT_URI
        
        # Redirigimos al usuario a la página de autorización de Google
        return redirect(auth_url)
    
    except Exception as e:
        logger.error(f"Error al iniciar el flujo OAuth: {str(e)}")
        messages.error(request, f"Error al conectar con Google: {str(e)}")
        return redirect(request.GET.get('next', reverse('reuniones:listar_reuniones_ejecutivo')))

@login_required
def oauth_callback(request):
    """Maneja la respuesta de Google después de la autorización"""
    try:
        # Verificamos el estado para prevenir CSRF
        state = request.session.get('oauth_state', '')
        if state != request.GET.get('state', ''):
            raise ValueError("Estado de verificación inválido")
        
        # Reconstruimos el flujo desde los datos de sesión
        flow = Flow.from_client_config(
            client_config=request.session['flow_client_config'],
            scopes=request.session['flow_scopes'],
            redirect_uri=request.session['flow_redirect_uri']
        )
        
        # Finalizamos el flujo con el código de autorización
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        
        # Obtenemos las credenciales
        credentials = flow.credentials
        
        # Obtenemos el usuario base correspondiente
        usuario = usuario_base.objects.get(correo=request.user.email)
        
        # Guardamos o actualizamos el token en la base de datos
        token, created = GoogleToken.objects.update_or_create(
            user=usuario,
            defaults={
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token or '',
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': ' '.join(credentials.scopes) if credentials.scopes else '',
                'expiry': credentials.expiry
            }
        )
        
        # Mensaje de éxito
        if created:
            messages.success(request, "¡Tu cuenta de Google ha sido conectada exitosamente!")
        else:
            messages.success(request, "¡Tu conexión con Google ha sido actualizada exitosamente!")
        
        # Limpiamos los datos de la sesión que ya no necesitamos
        for key in ['flow_client_config', 'flow_scopes', 'flow_redirect_uri', 'oauth_state']:
            if key in request.session:
                del request.session[key]
        
        # Redirigimos a la página que solicitó la autenticación
        next_url = request.session.get('oauth_next_url', reverse('reuniones:listar_reuniones_ejecutivo'))
        if 'oauth_next_url' in request.session:
            del request.session['oauth_next_url']
            
        return redirect(next_url)
    
    except Exception as e:
        logger.error(f"Error en el callback de OAuth: {str(e)}")
        messages.error(request, f"Error al procesar la autorización de Google: {str(e)}")
        return redirect('reuniones:listar_reuniones_ejecutivo')

@login_required
def google_disconnect(request):
    """Desconectar la cuenta de Google"""
    try:
        usuario = usuario_base.objects.get(correo=request.user.email)
        GoogleToken.objects.filter(user=usuario).delete()
        messages.success(request, "Cuenta de Google desconectada exitosamente")
    except Exception as e:
        logger.error(f"Error al desconectar Google: {str(e)}")
        messages.error(request, f"Error al desconectar la cuenta de Google: {str(e)}")
    
    return redirect(request.META.get('HTTP_REFERER', reverse('reuniones:listar_reuniones_ejecutivo')))

# Añade esta función al final del archivo
@login_required
def diagnostico_oauth(request):
    """Vista de diagnóstico para depurar problemas de OAuth"""
    if not request.user.is_superuser:
        messages.error(request, "Solo administradores pueden acceder a esta página")
        return redirect('reuniones:listar_reuniones_ejecutivo')
    
    diagnostico = [
        f"GOOGLE_OAUTH_CLIENT_ID: {settings.GOOGLE_OAUTH_CLIENT_ID[:10]}... (longitud: {len(settings.GOOGLE_OAUTH_CLIENT_ID)})",
        f"GOOGLE_OAUTH_REDIRECT_URI: {settings.GOOGLE_OAUTH_REDIRECT_URI}"
    ]
    
    # Verificar si hay algún problema obvio
    posibles_problemas = []
    
    if not settings.GOOGLE_OAUTH_CLIENT_ID:
        posibles_problemas.append("⚠️ CLIENT_ID está vacío")
    
    if not settings.GOOGLE_OAUTH_CLIENT_SECRET:
        posibles_problemas.append("⚠️ CLIENT_SECRET está vacío")
    
    if not settings.GOOGLE_OAUTH_REDIRECT_URI:
        posibles_problemas.append("⚠️ REDIRECT_URI está vacía")
    elif not settings.GOOGLE_OAUTH_REDIRECT_URI.startswith(('http://', 'https://')):
        posibles_problemas.append("⚠️ REDIRECT_URI no comienza con http:// o https://")
    
    # Añadir problemas detectados al diagnóstico
    if posibles_problemas:
        diagnostico.append("\nProblemas detectados:")
        diagnostico.extend(posibles_problemas)
    
    # Añadir sugerencias
    diagnostico.append("\nSugerencias:")
    diagnostico.append("1. Verifica que las credenciales en settings.py sean correctas")
    diagnostico.append("2. Asegúrate de que la URI de redirección coincida exactamente con la configurada en Google Cloud Console")
    diagnostico.append("3. Verifica que la cuenta de correo que estás usando esté en la lista de usuarios de prueba en la consola de Google")
    
    return render(request, 'reuniones/diagnostico_oauth.html', {
        'diagnostico': diagnostico,
    })