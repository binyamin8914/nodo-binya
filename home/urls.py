from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('detalle/<int:id>/', views.detalle, name='detalle'),
    path('contacto/', views.contacto, name='contacto'),
    path('postula/', views.postula, name='postula'),
]
