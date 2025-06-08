from django.urls import path
from django.shortcuts import render
from .views import EmpresaStepView, ContactoStepView, DesafioStepView

urlpatterns = [
    path('empresa', EmpresaStepView.as_view(), name='empresa_step'),
    path('contacto', ContactoStepView.as_view(), name='contacto_step'),
    path('desafio', DesafioStepView.as_view(), name='desafio_step'),
    path('complete', lambda request: render(request, 'form_complete.html'), name='form_complete'),
]