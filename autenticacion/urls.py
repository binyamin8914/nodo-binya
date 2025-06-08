from django.urls import path
from .views import *

urlpatterns = [
    path('login/', custom_login, name='login'),
    path('registro/', registro_view, name='registro'),
    path('logout/', logout_view, name='logout'),
    path('usuario/', pagina_usuario, name='pagina_usuario'),
    path('ejecutivo/', pagina_ejecutivo, name='pagina_ejecutivo'),
    path('cambiar-password/', cambiar_password, name='cambiar_password'),
]