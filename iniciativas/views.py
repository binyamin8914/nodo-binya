from django.shortcuts import render, redirect
from django.views import View
from .forms import EmpresaForm, ContactoEmpresaForm, PostulacionIniciativaForm
from .models import PostulacionIniciativa
from administracion.models import Empresa, usuario_base
from django.db import transaction
from django.contrib import messages
from django.shortcuts import get_object_or_404
from desafios.models import Desafio
class EmpresaStepView(View):
    def get(self, request,id):
        request.session['desafio_id'] = id
        initial_data = request.session.get('empresa_data', {})
        form = EmpresaForm(initial=initial_data)
        return render(request, 'form_empresa_i.html', {'form': form})
    
    def post(self, request,id):
        form = EmpresaForm(request.POST)
        if form.is_valid():
            request.session['empresa_data'] = form.cleaned_data
            return redirect('contacto_step_i')
        return render(request, 'form_empresa_i.html', {'form': form})

class ContactoStepView(View):
    def get(self, request):
        initial_data = request.session.get('contacto_data', {})
        form = ContactoEmpresaForm(initial=initial_data)
        return render(request, 'form_contacto_i.html', {'form': form})
    
    def post(self, request):
        form = ContactoEmpresaForm(request.POST)
        if form.is_valid():
            request.session['contacto_data'] = form.cleaned_data
            return redirect('iniciativa_step_i')
        return render(request, 'form_contacto_i.html', {'form': form})

class IniciativaStepView(View):
    def get(self, request):
        initial_data = request.session.get('iniciativa_data', {})
        form = PostulacionIniciativaForm(initial=initial_data)
        return render(request, 'form_iniciativa.html', {'form': form})
    
    def post(self, request):
        form = PostulacionIniciativaForm(request.POST)
        
        if form.is_valid():
            request.session['iniciativa_data'] = form.cleaned_data
            print(request.session.get('empresa_data'))
            print(request.session.get('contacto_data'))
            print(request.session.get('iniciativa_data'))
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
                    desafio_id = request.session.get('desafio_id')
                    if desafio_id==0:
                        desafio = None
                    else:
                        desafio = get_object_or_404(Desafio, id=desafio_id)
                    # Guardar Desafío
                    PostulacionIniciativa.objects.create(
                        empresa=empresa,
                        contacto=contacto,
                        desafio=desafio,
                        descripcion=form.cleaned_data['descripcion'],
                        pregunta=form.cleaned_data['pregunta'],
                        origen=form.cleaned_data['origen'],

                    )
                
                # Limpiar datos de la sesión
                request.session.pop('empresa_data', None)
                request.session.pop('contacto_data', None)
                request.session.pop('iniciativa_data', None)
                return redirect('form_complete_i')  

            except Exception as e:
                print("errorsete")
                print(e)
                return render(request, 'form_error_i.html')

        return render(request, 'form_iniciativa.html', {'form': form})
