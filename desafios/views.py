from django.shortcuts import render, redirect
from django.views import View
from .forms import EmpresaForm, ContactoEmpresaForm, PostulacionDesafioForm
from .models import PostulacionDesafio
from administracion.models import Empresa, usuario_base
from django.db import transaction
from django.contrib import messages

class EmpresaStepView(View):
    def get(self, request):
        initial_data = request.session.get('empresa_data', {})
        form = EmpresaForm(initial=initial_data)
        return render(request, 'form_empresa.html', {'form': form})
    
    def post(self, request):
        form = EmpresaForm(request.POST)
        if form.is_valid():
            request.session['empresa_data'] = form.cleaned_data
            return redirect('contacto_step')
        return render(request, 'form_empresa.html', {'form': form})

class ContactoStepView(View):
    def get(self, request):
        initial_data = request.session.get('contacto_data', {})
        form = ContactoEmpresaForm(initial=initial_data)
        return render(request, 'form_contacto.html', {'form': form})
    
    def post(self, request):
        form = ContactoEmpresaForm(request.POST)
        if form.is_valid():
            request.session['contacto_data'] = form.cleaned_data
            return redirect('desafio_step')
        return render(request, 'form_contacto.html', {'form': form})

class DesafioStepView(View):
    def get(self, request):
        initial_data = request.session.get('desafio_data', {})
        form = PostulacionDesafioForm(initial=initial_data)
        return render(request, 'form_desafio.html', {'form': form})
    
    def post(self, request):
        form = PostulacionDesafioForm(request.POST)
        if form.is_valid():
            request.session['desafio_data'] = form.cleaned_data
            print(request.session.get('empresa_data'))
            print(request.session.get('contacto_data'))
            print(request.session.get('desafio_data'))
            try:
                with transaction.atomic():
                    # Guardar Empresa
                    empresa_data = request.session.get('empresa_data')
                    empresa = Empresa.objects.create(**empresa_data)
                    
                    # Guardar Contacto
                    contacto_data = request.session.get('contacto_data')
                    contacto = usuario_base.objects.create(
                        empresa=empresa, **contacto_data
                    )
                    
                    # Guardar Desafío
                    PostulacionDesafio.objects.create(
                        empresa=empresa,
                        contacto=contacto,
                        descripcionInicial=form.cleaned_data['descripcionInicial'],
                        desafioFrase=form.cleaned_data['desafioFrase'],
                        presupuesto=form.cleaned_data['presupuesto'],
                        pregunta=form.cleaned_data['pregunta'],
                        origen=form.cleaned_data['origen'],
                    )
                
                # Limpiar datos de la sesión
                request.session.pop('empresa_data', None)
                request.session.pop('contacto_data', None)
                request.session.pop('desafio_data', None)
                return redirect('form_complete')  

            except Exception as e:
                print("errorsete")
                print(e)
                return render(request, 'form_error.html')

        return render(request, 'form_desafio.html', {'form': form})
