from django.urls import path
from django.shortcuts import render
from .views import EmpresaStepView, ContactoStepView, IniciativaStepView

urlpatterns = [
    path('empresa_i/<int:id>', EmpresaStepView.as_view(), name='empresa_step_i'),
    path('contacto_i', ContactoStepView.as_view(), name='contacto_step_i'),
    path('iniciativa_i', IniciativaStepView.as_view(), name='iniciativa_step_i'),
    path('complete_i', lambda request: render(request, 'form_complete_i.html'), name='form_complete_i'),
]