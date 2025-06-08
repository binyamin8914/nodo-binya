from django.shortcuts import render, redirect, get_object_or_404
from desafios.models import Desafio, PostulacionDesafio
from .models import Empresa, usuario_base, Documento, solicitudContacto , Match, Objetivo, Metrica, Evaluacion, Actividad
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from .forms import DesafioForm, DesafioBulkUpdateForm, PostForm, IniciativaForm, MatchForm, ObjetivoForm, MetricaForm, EvaluacionForm, ActividadForm, EjecutivoCreationForm
from blog.models import Post
from django.urls import reverse
from django.http import Http404,FileResponse, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
import os
from django.db.models import Q
from iniciativas.models import PostulacionIniciativa, Iniciativa
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password 

@login_required  
def serve_document(request, filename):
    file_path = os.path.join('administracion/documentos', filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'inline; filename={os.path.basename(file_path)}'
            return response
    else:
        raise Http404("File not found")




#MATCHES
def matches(request):
    query = request.GET.get('q', '')  # Parámetro de búsqueda
    # busqueda 
    matches = Match.objects.filter(isActive=True)
    if query:
        matches = matches.filter(
            Q(desafio__nombreDesafio__icontains=query) | 
            Q(iniciativa__titulo__icontains=query) |
            Q(id__icontains=query)   
        )
    else:
        matches = Match.objects.select_related('desafio', 'iniciativa').filter(isActive=True)
    return render(request, 'matches.html', {'active_page': 'matches', 'title': 'Matches','matches': matches,'query': query  })   

from django.shortcuts import get_object_or_404

def crear_match(request, desafio_id, iniciativa_id, match_id=None):
    desafio = Desafio.objects.filter(id=desafio_id).first()
    iniciativa = Iniciativa.objects.filter(id=iniciativa_id).first()
    match = None

    if match_id:
        match = get_object_or_404(Match, id=match_id)

    if request.method == 'POST':
        form = MatchForm(request.POST, instance=match)
        if form.is_valid():
            match = form.save(commit=False)
            match.ejecutivo = request.user  # El usuario en sesión
            match.save()
            return redirect('matches')
        else:
            print(form.errors)
    else:
        if desafio and iniciativa:
            form = MatchForm(initial={
                'desafio': desafio,
                'iniciativa': iniciativa
            })
        else:
            form = MatchForm(instance=match)

    form.initial['ejecutivo'] = request.user
    return render(request, 'crear_match.html', {
        'form': form,
        'desafio': desafio,
        'iniciativa': iniciativa,
        'active_page': 'crear_match',
        'match': match,  
    })

def verEvaluacion(request, id):
    evaluacion = get_object_or_404(Evaluacion, id=id)

    # Pasar los objetos al contexto
    context = {
        'evaluacion': evaluacion,
        'active_page': 'matches',   
    }

    return render(request, 'ver_evaluacion.html', context)

def eliminarMatch(request, id):
    if request.method == 'POST':
        match = get_object_or_404(Match, id=id)
        match.isActive = False
        match.save()
    return redirect('matches') 




def gestionar_objetivo(request, match_id, objetivo_id=None):
    match = get_object_or_404(Match, id=match_id)
    objetivo = None

    # Si se proporciona un objetivo_id, estamos editando un objetivo existente
    if objetivo_id:
        objetivo = get_object_or_404(Objetivo, id=objetivo_id, match=match)

    if request.method == 'POST':
        form = ObjetivoForm(request.POST, instance=objetivo)
        if form.is_valid():
            objetivo = form.save(commit=False)
            objetivo.match = match
            objetivo.save()
            return redirect('matches')
    else:
        form = ObjetivoForm(instance=objetivo)

    return render(request, 'gestionar_objetivo.html', {
        'form': form,
        'match': match,
        'objetivo': objetivo,
        'active_page': 'matches',
    })




def gestionar_metrica(request, objetivo_id, metrica_id=None):
    objetivo = get_object_or_404(Objetivo, id=objetivo_id)
    metrica = None

    if metrica_id:
        metrica = get_object_or_404(Metrica, id=metrica_id, objetivo=objetivo)

    if request.method == 'POST':
        form = MetricaForm(request.POST, instance=metrica)
        if form.is_valid():
            metrica = form.save(commit=False)
            metrica.objetivo = objetivo
            metrica.save()
            return redirect('matches')
    else:
        form = MetricaForm(instance=metrica)

    return render(request, 'gestionar_metrica.html', {
        'form': form,
        'objetivo': objetivo,
        'metrica': metrica,
        'active_page': 'matches',
    })


def gestionar_evaluacion(request, metrica_id, evaluacion_id=None):
    metrica = get_object_or_404(Metrica, id=metrica_id)
    evaluacion = None

    # Si se proporciona un evaluacion_id, estamos editando una evaluación existente
    if evaluacion_id:
        evaluacion = get_object_or_404(Evaluacion, id=evaluacion_id, metrica=metrica)

    if request.method == 'POST':
        form = EvaluacionForm(request.POST, instance=evaluacion)
        if form.is_valid():
            evaluacion = form.save(commit=False)
            evaluacion.metrica = metrica
            evaluacion.save()
            return redirect('matches')
    else:
        form = EvaluacionForm(instance=evaluacion)

    return render(request, 'gestionar_evaluacion.html', {
        'form': form,
        'metrica': metrica,
        'evaluacion': evaluacion,
        'active_page': 'matches',
    })



def gestionar_actividad(request, metrica_id, actividad_id=None):
    metrica = get_object_or_404(Metrica, id=metrica_id)
    actividad = None

    # Si se proporciona un actividad_id, estamos editando una actividad existente
    if actividad_id:
        actividad = get_object_or_404(Actividad, id=actividad_id, metrica=metrica)

    if request.method == 'POST':
        form = ActividadForm(request.POST, instance=actividad)
        if form.is_valid():
            actividad = form.save(commit=False)
            actividad.metrica = metrica
            actividad.save()
            return redirect('matches')
    else:
        form = ActividadForm(instance=actividad)

    return render(request, 'gestionar_actividad.html', {
        'form': form,
        'metrica': metrica,
        'actividad': actividad,
        'active_page': 'matches',
    })





#POSTULACIONES DESAFIOS

def postulacionesDesafios(request):
    # Obtener parámetros de búsqueda y filtro de estado
    query = request.GET.get('q', '')  # Parámetro de búsqueda
    estado = request.GET.get('estado', '')  # Filtro de estado

    # Obtener todas las postulaciones activas
    postulaciones = PostulacionDesafio.objects.select_related('empresa').filter(isActive=True)

    # busqueda 
    if query:
        postulaciones = postulaciones.filter(
            Q(empresa__nombre__icontains=query) | # buscar por empresa
            Q(id__icontains=query) | # buscar por id
            Q(desafioFrase__icontains=query)   # buscar por frase
        )

    
    if estado:
        postulaciones = postulaciones.filter(estado=estado)

    # porfecha
    postulaciones = postulaciones.order_by('-fecha')

    return render(request, 'postulaciones_desafio.html', {
        'active_page': 'postulacionesDesafios',
        'title': 'Postulaciones',
        'postulaciones': postulaciones,
        'estado_seleccionado': estado,
        'query': query,  
    })

def verPostulacionDesafio(request, id):
    postulacion = get_object_or_404(PostulacionDesafio.objects.select_related('empresa', 'contacto'), id=id)
    return render(request, 'ver_postulacion_desafio.html',{'active_page': 'postulacionesDesafios', 'title': 'Postulaciones' ,'postulacion': postulacion})

def depurar_desafio(request,id):
    postulacion = get_object_or_404(PostulacionDesafio, id=id)
    # Si ya existe un desafío relacionado con esta postulación, se edita.
    desafio = Desafio.objects.filter(postulacion=postulacion).first()
    existing_documents=[]
    # Si no existe un desafío relacionado, se crea uno nuevo.
    if not desafio:
        print("No existe desafio")
        desafio = Desafio(postulacion=postulacion,empresa=postulacion.empresa,contacto=postulacion.contacto,ejecutivo=request.user )     
        print(desafio)
    else:
        existing_documents = Documento.objects.filter(object_id=desafio.id,content_type=ContentType.objects.get_for_model(Desafio))
    if request.method == 'POST':
        print(request.POST)
        form = DesafioForm(request.POST, request.FILES, instance=desafio)
        form.instance.postulacion = postulacion
        form.instance.empresa = postulacion.empresa
        form.instance.contacto = postulacion.contacto
        form.instance.ejecutivo = request.user
        documentos_a_eliminar = request.POST.getlist('eliminar_documentos')
        print(form.errors)
        if form.is_valid():
            desafio = form.save(commit=False)  # Guarda el formulario  sin confirmarlo
            desafio.postulacion = postulacion
            desafio.empresa = postulacion.empresa
            desafio.contacto = postulacion.contacto
            desafio.ejecutivo = request.user
            postulacion.estado = 'Depurado'
            postulacion.save()
            print(desafio)
            desafio.save()
            # Elimina los documentos seleccionados
            for doc_id in documentos_a_eliminar:
                try:
                    documento = Documento.objects.get(id=doc_id)
                    documento.delete()
                except Documento.DoesNotExist:
                    continue  

            content_type = ContentType.objects.get_for_model(Desafio)
            archivos = request.FILES.getlist('documentos')
            if archivos:  
                content_type = ContentType.objects.get_for_model(Desafio)
                for archivo in archivos:
                    Documento.objects.create(
                        archivo=archivo,
                        nombre=archivo.name,
                        content_type=content_type,
                        object_id=desafio.id
                    )

            print('Desafío guardado')
        return redirect('desafios' )
    else: 
        form = DesafioForm(instance=desafio)

    return render(request, 'depurar_desafio.html', {'active_page': 'postulacionesDesafios', 'title': 'Postulaciones','form': form, 'postulacion': postulacion,'existing_documents': existing_documents})

def eliminarPostulacionDesafio(request, id):
    if request.method == 'POST':
        postulacion = get_object_or_404(PostulacionDesafio, id=id)
        postulacion.isActive = False
        postulacion.save()
    return redirect('postulaciones_desafios') 

def cambiar_estado_postulacion(request, id):
    postulacion = get_object_or_404(PostulacionDesafio, id=id)
    print(postulacion.estado)
    if postulacion.estado == "Por Depurar" or postulacion.estado == "Depurado":
        postulacion.estado = "Abandonado"
    elif postulacion.estado == "Abandonado":
        postulacion.estado = "Por Depurar"
    else:
        messages.success(request, f"Hay un error con el estado '{postulacion.estado}'.")
    print(postulacion.estado)
    postulacion.save()
    messages.success(request, f"El estado de la postulación se ha actualizado a '{postulacion.estado}'.")

    return redirect('postulaciones_desafios')



#DESAFIOS

def desafios(request):
    
    query = request.GET.get('q', '')

    desafios = Desafio.objects.select_related('empresa', 'contacto').filter(isActive=True)

    if query:
        desafios = desafios.filter(
            Q(nombreDesafio__icontains=query) |
            Q(id__icontains=query) |  # busca por nombre
            Q(empresa__nombre__icontains=query)  # busca por empresa
        )

    
    return render(request, 'desafios_depurados.html', {
        'active_page': 'desafios',
        'title': 'Desafíos',
        'desafios': desafios,
        'query': query,  
    })

def verDesafio(request, id):
    desafio = get_object_or_404(Desafio.objects.select_related('empresa', 'contacto','postulacion'), id=id)
    documentos = Documento.objects.filter(content_type=ContentType.objects.get_for_model(Desafio), object_id=id)
    return render(request, 'ver_desafio.html',{'active_page': 'desafios', 'title': 'Desafios' ,'desafio': desafio, 'documentos': documentos})

def eliminarDesafio(request, id):
    if request.method == 'POST':
        desafio = get_object_or_404(Desafio, id=id)
        desafio.isActive = False
        desafio.save()
    return redirect('desafios') 

def actualizar_check_masivo(request):
    if request.method == 'POST':
        desafios = Desafio.objects.all()

        for desafio in desafios:
            # principal
            isPrincipal_checked = f'isPrincipal_{desafio.id}' in request.POST
            desafio.isPrincipal = isPrincipal_checked
            
            # show 
            show_checked = f'show_{desafio.id}' in request.POST
            desafio.show = show_checked
            desafio.save()
            if isPrincipal_checked:
                desafio.show = True
                desafio.save()

        return redirect('desafios') 

    return redirect('desafios') 



#EMPRESAS
def empresas(request):
    empresas = Empresa.objects.filter(isActive=True)
    return render(request, 'empresas.html', {'active_page': 'empresas', 'title': 'Empresas','empresas': empresas})

def verEmpresa(request, id):
    empresa = get_object_or_404(Empresa.objects, id=id)
    contactos = usuario_base.objects.filter(empresa=empresa.id, es_activo=True)
    return render(request, 'ver_empresa.html',{'active_page': 'empresas', 'title': 'Empresas' ,'empresa': empresa, 'contactos': contactos})







#POSTULACIONES INICIATIVAS
def postulacionesIniciativas(request):
    # Obtener parámetros de búsqueda y filtro de estado
    query = request.GET.get('q', '')  # Parámetro de búsqueda
    estado = request.GET.get('estado', '')  # Filtro de estado
    # Obtener todas las postulaciones activas
    postulaciones = PostulacionIniciativa.objects.select_related('empresa').filter(isActive=True)

    # busqueda 
    if query:
        postulaciones = postulaciones.filter(
            Q(empresa__nombre__icontains=query) | # buscar por empresa
            Q(id__icontains=query) | # buscar por id
            Q(titulo__icontains=query)   # titulo
        )

    if estado:
        postulaciones = postulaciones.filter(estado=estado)

    # porfecha
    postulaciones = postulaciones.order_by('-fecha')

    return render(request, 'postulaciones_iniciativa.html', {
        'active_page': 'postulacionesIniciativas',
        'title': 'Postulaciones',
        'postulaciones': postulaciones,
        'estado_seleccionado': estado,
        'query': query,  
    })

def verPostulacionIniciativa(request, id):
    postulacion = get_object_or_404(PostulacionIniciativa.objects.select_related('empresa', 'contacto'), id=id)
    return render(request, 'ver_postulacion_iniciativa.html',{'active_page': 'postulacionesIniciativas', 'title': 'Postulaciones' ,'postulacion': postulacion})

def eliminarPostulacionIniciativa(request, id):
    if request.method == 'POST':
        postulacion = get_object_or_404(PostulacionIniciativa, id=id)
        postulacion.isActive = False
        postulacion.save()
    return redirect('postulaciones_iniciativas') 
def cambiar_estado_postulacion_i(request, id):
    postulacion = get_object_or_404(PostulacionIniciativa, id=id)
    print(postulacion.estado)
    if postulacion.estado == "Por Depurar" or postulacion.estado == "Depurado" or postulacion.estado == "Por depurar":
        postulacion.estado = "Abandonado"
    elif postulacion.estado == "Abandonado":
        postulacion.estado = "Por Depurar"
    else:
        messages.success(request, f"Hay un error con el estado '{postulacion.estado}'.")
    print(postulacion.estado)
    postulacion.save()
    messages.success(request, f"El estado de la postulación se ha actualizado a '{postulacion.estado}'.")

    return redirect('postulaciones_iniciativas')

def depurar_iniciativa(request,id):
    postulacion = get_object_or_404(PostulacionIniciativa, id=id)
    # Si ya existe un desafío relacionado con esta postulación, se edita.
    iniciativa = Iniciativa.objects.filter(postulacion=postulacion).first()
    existing_documents=[]
    # Si no existe un desafío relacionado, se crea uno nuevo.
    if not iniciativa:
        print("No existe iniciativa")
        iniciativa = Iniciativa(postulacion=postulacion,empresa=postulacion.empresa,contacto=postulacion.contacto,ejecutivo=request.user,desafio=postulacion.desafio )     
        print(iniciativa)
    else:
        existing_documents = Documento.objects.filter(object_id=iniciativa.id,content_type=ContentType.objects.get_for_model(Iniciativa))
    if request.method == 'POST':
        print(request.POST)
        action = request.POST.get('action')
        form = IniciativaForm(request.POST, request.FILES, instance=iniciativa)
        form.instance.postulacion = postulacion
        form.instance.desafio = postulacion.desafio
        form.instance.empresa = postulacion.empresa
        form.instance.contacto = postulacion.contacto
        form.instance.ejecutivo = request.user
        documentos_a_eliminar = request.POST.getlist('eliminar_documentos')
        print(form.errors)
        if form.is_valid():
            iniciativa = form.save(commit=False)  # Guarda el formulario  sin confirmarlo
            iniciativa.postulacion = postulacion
            iniciativa.empresa = postulacion.empresa
            iniciativa.contacto = postulacion.contacto
            iniciativa.ejecutivo = request.user

            postulacion.estado = 'Depurado'
            postulacion.save()

            print(iniciativa)
            iniciativa.save()
            # Elimina los documentos seleccionados
            for doc_id in documentos_a_eliminar:
                try:
                    documento = Documento.objects.get(id=doc_id)
                    documento.delete()
                except Documento.DoesNotExist:
                    continue  

            content_type = ContentType.objects.get_for_model(Iniciativa)
            archivos = request.FILES.getlist('documentos')
            if archivos:  
                content_type = ContentType.objects.get_for_model(Iniciativa)
                for archivo in archivos:
                    Documento.objects.create(
                        archivo=archivo,
                        nombre=archivo.name,
                        content_type=content_type,
                        object_id=iniciativa.id
                    )

            print('Iniciativa guardada')

            if action == 'save_and_redirect':
                return redirect(reverse('crear_match', args=[iniciativa.desafio.id, iniciativa.id]))
        return redirect('iniciativas' )
    else: 
        form = IniciativaForm(instance=iniciativa)

    return render(request, 'depurar_iniciativa.html', {'active_page': 'postulacionesIniciativas', 'title': 'Postulaciones','form': form, 'postulacion': postulacion,'existing_documents': existing_documents})


#INICIATIVAS

def iniciativas(request):
    
    query = request.GET.get('q', '')

    iniciativas = Iniciativa.objects.select_related('empresa', 'contacto').filter(isActive=True)

    if query:
        iniciativas = iniciativas.filter(
            Q(desafio__nombreDesafio__icontains=query) |
            Q(postulacion__nombreDesafio__icontains=query) |
            Q(id__icontains=query) |  # busca por id
            Q(empresa__nombre__icontains=query)  # busca por empresa
        )

    
    return render(request, 'iniciativas_depuradas.html', {
        'active_page': 'iniciativas',
        'title': 'Iniciativas',
        'iniciativas': iniciativas,
        'query': query,  
    })

def verIniciativa(request, id):
    iniciativa = get_object_or_404(Iniciativa.objects.select_related('empresa', 'contacto','postulacion'), id=id)
    documentos = Documento.objects.filter(content_type=ContentType.objects.get_for_model(Iniciativa), object_id=id)
    return render(request, 'ver_iniciativa.html',{'active_page': 'iniciativas', 'title': 'Iniciativa' ,'iniciativa': iniciativa, 'documentos': documentos})


def eliminarIniciativa(request, id):
    if request.method == 'POST':
        iniciativa = get_object_or_404(Iniciativa, id=id)
        iniciativa.isActive = False
        iniciativa.save()
    return redirect('iniciativas') 



#BLOG
def crear_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        action = request.POST.get('action')

        if form.is_valid():
            if action == 'publicar':
                print('publicar')
                form.publico = True  
                form.save()  
                return redirect(reverse('post', kwargs={'slug': form.instance.slug}))
            else:
                print('guardar')
                form.publico = False
                form.save()  
                return redirect('posts')  
    else:
        form = PostForm()
    return render(request, 'crear_post.html', {'active_page': 'crear_post', 'title': 'Crear Post','form': form})

def posts(request):
    posts = Post.objects.filter(is_active=True).order_by('-fecha')
    return render(request, 'posts.html', {'active_page': 'posts','title': 'Posts','posts': posts})

def editar_post(request, id):
    post = get_object_or_404(Post, id=id)
    
    if request.method == 'POST':

        form = PostForm(request.POST, request.FILES, instance=post)
        action = request.POST.get('action')
        if form.is_valid():
            print(form)
            if not form.cleaned_data['portada']:
                post.portada =  'django-summernote/portadas/default.png'

            if action == 'publicar':
                print('publicar')
                post.publico = True  
                form.save()  
                return redirect(reverse('post', kwargs={'slug': form.instance.slug}))
            else:
                print('guardar')
                post.publico = False
                form.save()  
                return redirect('posts')  
            
            
    else:
        
        form = PostForm(instance=post)
    
    return render(request, 'editar_post.html', {'active_page': 'posts','title': 'Posts','form': form, 'post': post})

def eliminarPost(request, id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=id)
        post.is_active = False
        post.save()
    return redirect('posts') 

def actualizar_check_masivo_post(request):
    if request.method == 'POST':
        posts = Post.objects.all()

        for post in posts:
            is_public_checked = f'publico_{post.id}' in request.POST
            post.publico = is_public_checked
            post.save()

        return redirect('posts')

    return redirect('posts') 




#Solicitudes de contacto
def solicitudes_contacto(request):
    solicitudes= solicitudContacto.objects.filter(isActive=True).order_by('-fecha')
    return render(request, 'solicitudes_contacto.html', {'active_page': 'solicitudes_contacto', 'title': 'Solicitudes de contacto','solicitudes': solicitudes})

def verSolicitud(request, id):
    solicitud = get_object_or_404(solicitudContacto.objects, id=id)
    return render(request, 'ver_solicitud.html',{'active_page': 'solicitudes_contacto', 'title': 'Solicitudes de contacto','solicitud': solicitud})

def eliminarSolicitud(request, id):
    if request.method == 'POST':
        solicitud = get_object_or_404(solicitudContacto, id=id)
        solicitud.isActive = False
        solicitud.save()
    return redirect('solicitudes_contacto')  

def metabase(request):

    import jwt
    import time

    METABASE_SITE_URL = "https://metabase.camiongo.com"
    METABASE_SECRET_KEY = "0a68a280256d5c23aa1994bd64809b297106e0d5511ac97fc74da9b90c378473"

    payload = {
    "resource": {"dashboard": 101},
    "params": {
        
    },
    "exp": round(time.time()) + (60 * 10) # 10 minute expiration
    }
    token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")

    iframeUrl = METABASE_SITE_URL + "/embed/dashboard/" + token + "#bordered=true&titled=true"

    return render(request, "dashboard.html", {'active_page': 'metabase', 'title': 'Dashboard',"dashboard_url": iframeUrl})


#Gestion de ejecutivos

def verEmpresa(request, id):
    empresa = get_object_or_404(Empresa.objects, id=id)
    contactos = usuario_base.objects.filter(empresa=empresa.id, es_activo=True)
    return render(request, 'ver_empresa.html',{'active_page': 'empresas', 'title': 'Empresas' ,'empresa': empresa, 'contactos': contactos})

# Añadir esta función para verificar si el usuario es administrador
def es_admin(user):
    return user.is_superuser

# Añadir estas vistas al archivo
@user_passes_test(es_admin)
def gestionar_usuarios(request):
    usuarios = usuario_base.objects.filter(rol="ejecutivo", es_activo=True)
    return render(request, 'gestionar_usuarios.html', {
        'active_page': 'usuarios',
        'title': 'Gestión de Usuarios',
        'usuarios': usuarios
    })

# Modificar la función crear_ejecutivo para evitar duplicados
@user_passes_test(es_admin)
def crear_ejecutivo(request):
    if request.method == 'POST':
        form = EjecutivoCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            email = form.cleaned_data.get('email')
            
            # Verificar si ya existe un usuario_base con este correo
            usuario_existente = usuario_base.objects.filter(correo=email).first()
            
            if not usuario_existente:
                # Crear registro en usuario_base solo si no existe
                usuario_base_obj = usuario_base.objects.create(
                    nombre=form.cleaned_data.get('nombre_completo'),
                    correo=email,
                    contraseña=make_password(form.cleaned_data.get('password1')),  # Cifrar la contraseña
                    rol="ejecutivo",
                    es_activo=True,
                    cargo=form.cleaned_data.get('cargo'),
                    telefono=form.cleaned_data.get('telefono') or "",
                    empresa=None  # Los ejecutivos no están asociados a una empresa específica
                )
            else:
                # Actualizar el usuario existente
                usuario_existente.nombre = form.cleaned_data.get('nombre_completo')
                usuario_existente.rol = "ejecutivo"
                usuario_existente.es_activo = True
                usuario_existente.cargo = form.cleaned_data.get('cargo')
                usuario_existente.telefono = form.cleaned_data.get('telefono') or ""
                usuario_existente.save()
            
            messages.success(request, f'Usuario ejecutivo {user.username} creado correctamente.')
            return redirect('gestionar_usuarios')
    else:
        form = EjecutivoCreationForm()
    
    return render(request, 'crear_ejecutivo.html', {
        'active_page': 'usuarios',
        'title': 'Crear Usuario Ejecutivo',
        'form': form
    })

@user_passes_test(es_admin)
def desactivar_ejecutivo(request, id):
    usuario = get_object_or_404(usuario_base, id=id, rol="ejecutivo")
    usuario.es_activo = False
    usuario.save()
    
    # También desactivar el usuario de Django si existe
    try:
        user = User.objects.get(email=usuario.correo)
        user.is_active = False
        user.save()
    except User.DoesNotExist:
        pass
    
    messages.success(request, f'Usuario ejecutivo {usuario.nombre} desactivado correctamente.')
    return redirect('gestionar_usuarios')
