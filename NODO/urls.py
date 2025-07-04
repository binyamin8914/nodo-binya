"""
URL configuration for NODO project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls.conf import include
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', include('home.urls')),
    path('autenticacion/', include('autenticacion.urls')),
    path('administracion/', include('administracion.urls')),
    path('admin/', admin.site.urls),
    path('postulacion/', include('desafios.urls')),
    path('postulacionIniciativa/', include('iniciativas.urls')),
    path('blog/', include('blog.urls')),
    path('captcha/', include('captcha.urls')),
    path('summernote/', include('django_summernote.urls')),
    path('reuniones/', include('reuniones.urls')),   
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)