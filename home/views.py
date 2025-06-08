from django.shortcuts import render,get_object_or_404
from desafios.models import Desafio
from administracion.forms import ContactoForm
# Create your views here.

def home(request):
    desafios = Desafio.objects.filter(isPrincipal=True)
    
    # Crear un contexto específico con los datos personalizados
    context = {
        'desafios': [
            {
                'id': desafio.id,
                'nombre': desafio.nombreDesafio,
                'pais': desafio.empresa.pais if desafio.empresa else None,
                'actividad': desafio.empresa.actividad if desafio.empresa else None,
                'imagen': desafio.imagen.url if desafio.imagen else None,
            }
            for desafio in desafios
        ]
    }
    
    return render(request, 'home.html', context)

def detalle(request,id):
    desafio = get_object_or_404(Desafio.objects.select_related('empresa', 'ejecutivo').filter(show=True), id=id)

    # datos especificos contexto
    contexto = {
        'id': desafio.id,
        'nombreDesafio': desafio.nombreDesafio,
        'descripcionDesafio': desafio.descripcionDesafio,
        'imagen': desafio.imagen.url,
        'empresa': {
            'pais': desafio.empresa.pais,
            'actividad': desafio.empresa.actividad,
        },
        'ejecutivo': {
            'nombre': desafio.ejecutivo.first_name,
            'apellido': desafio.ejecutivo.last_name,
            'correo': desafio.ejecutivo.email,
        }
    }

    return render(request, 'detalle_desafio.html', {'desafio': contexto})

def contacto(request):
    if request.method == 'POST':
        form = ContactoForm(request.POST)
        print(form.errors)
        if form.is_valid():
            form.save()
            print(form.cleaned_data)
            return render(request, 'contacto_success.html', {'form': form})
    return render(request, 'contacto.html', {'form': ContactoForm()})
    
def postula(request):
    return render(request, 'postula.html')