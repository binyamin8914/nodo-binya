from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'reuniones'

urlpatterns = [
    # Vistas para Ejecutivos
    path('ejecutivo/matches/', views.listar_matches_ejecutivo, name='listar_matches_ejecutivo'),  # Listar matches disponibles para agendar
    path('ejecutivo/reunion/nueva/<int:match_id>/', views.crear_reunion_directa, name='crear_reunion_directa'),  # Crear reunión directa
    path('ejecutivo/solicitudes/', views.listar_solicitudes_ejecutivo, name='listar_solicitudes_ejecutivo'),  # Listar solicitudes recibidas
    path('ejecutivo/solicitudes/<int:solicitud_id>/responder/', views.responder_solicitud, name='responder_solicitud'),  # Responder solicitud (aceptar/rechazar)
    path('ejecutivo/reuniones/', views.listar_reuniones_ejecutivo, name='listar_reuniones_ejecutivo'),  # Listar reuniones organizadas
    path('reuniones/<int:reunion_id>/', views.detalle_reunion, name='detalle_reunion'),  # Detalle de una reunión
    path('reuniones/editar/<int:reunion_id>/', views.editar_reunion, name='editar_reunion'),  # Editar reunión existente
    path('reuniones/eliminar/<int:reunion_id>/', views.eliminar_reunion, name='eliminar_reunion'),  # Eliminar reunión

    # Vistas para Contactos
    path('contacto/matches/', views.listar_matches_contacto, name='listar_matches'),  # Listar matches donde el usuario es contacto
    path('contacto/reunion/solicitar/<int:match_id>/', views.solicitar_reunion_contacto, name='solicitar_reunion'),  # Solicitar reunión
    path('contacto/solicitudes/', views.listar_solicitudes_contacto, name='listar_solicitudes'),  # Listar solicitudes enviadas
    path('contacto/reuniones/', views.listar_reuniones_contacto, name='listar_reuniones'),  # Listar reuniones donde el contacto participa

    # Google OAuth
    path('google/connect/', views.google_oauth_init, name='google_oauth_init'),  # Iniciar flujo OAuth de Google
    path('google/callback/', views.google_oauth_callback, name='google_oauth_callback'),  # Callback para OAuth
    path('google/disconnect/', views.google_disconnect, name='google_disconnect'),  # Desconectar cuenta de Google

    # Logout
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),  # Cerrar sesión
]