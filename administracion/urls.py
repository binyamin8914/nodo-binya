from django.urls import path, include
from . import views
from reuniones import views as reuniones_views
from django.conf import settings
from django.conf.urls.static import static
from .views import serve_document

urlpatterns = [
    path('documentos/<str:filename>/', views.serve_document, name='serve_document'),

    #DASHBOARD
    path('', views.metabase, name='metabase'),


    #MATCHES
    path('matches/', views.matches, name='matches'),
    path('matches/crear/<int:desafio_id>/<int:iniciativa_id>/', views.crear_match, name='crear_match'),
    path('matches/crear/<int:desafio_id>/<int:iniciativa_id>/<int:match_id>/', views.crear_match, name='editar_match'),
    path('matches/ver_evaluacion/<int:id>/', views.verEvaluacion, name='verevaluacion'),
    path('eliminar_match/<int:id>/', views.eliminarMatch, name='eliminarMatch'),

    #RELACIONADOS A MATCHES
    path('objetivos/gestionar/<int:match_id>/', views.gestionar_objetivo, name='crear_objetivo'),
    path('objetivos/gestionar/<int:match_id>/<int:objetivo_id>/', views.gestionar_objetivo, name='editar_objetivo'),

    path('metricas/gestionar/<int:objetivo_id>/', views.gestionar_metrica, name='crear_metrica'),
    path('metricas/gestionar/<int:objetivo_id>/<int:metrica_id>/', views.gestionar_metrica, name='editar_metrica'),
    
    path('evaluaciones/gestionar/<int:metrica_id>/', views.gestionar_evaluacion, name='crear_evaluacion'),
    path('evaluaciones/gestionar/<int:metrica_id>/<int:evaluacion_id>/', views.gestionar_evaluacion, name='editar_evaluacion'),
    
    path('actividades/gestionar/<int:metrica_id>/', views.gestionar_actividad, name='crear_actividad'),
    path('actividades/gestionar/<int:metrica_id>/<int:actividad_id>/', views.gestionar_actividad, name='editar_actividad'),
    
    #POSTULACIONES_DESAFIOS
    path('postulaciones_desafios/', views.postulacionesDesafios, name='postulaciones_desafios'),
    path('postulaciones_desafios/ver/<int:id>/', views.verPostulacionDesafio, name='verpostulacion'),
    path('postulaciones_desafios/depurar/<int:id>/', views.depurar_desafio, name='depurar_desafio'),
    path('eliminar_postulacionDesafio/<int:id>/', views.eliminarPostulacionDesafio, name='eliminarPostulacionDesafio'),
    path('postulacion/<int:id>/cambiar-estado/', views.cambiar_estado_postulacion, name='cambiar_estado_postulacion'),

    #DESAFIOS
    path('desafios/', views.desafios, name='desafios'),
    path('desafios/ver/<int:id>/', views.verDesafio, name='verdesafio'),
    path('desafios/actualizar_masivo/', views.actualizar_check_masivo, name='actualizar_check_masivo'),
    path('eliminar_Desafio/<int:id>/', views.eliminarDesafio, name='eliminarDesafio'),
    
    #EMPRESAS
    path('empresas/', views.empresas, name='empresas'),
    path('empresas/ver/<int:id>/', views.verEmpresa, name='verempresa'),

    #POSTULACIONES_INICIATIVAS
    path('postulaciones_iniciativas/', views.postulacionesIniciativas, name='postulaciones_iniciativas'),
    path('postulaciones_iniciativas/ver/<int:id>/', views.verPostulacionIniciativa, name='verpostulacion_i'),
    path('postulaciones_iniciativas/depurar/<int:id>/', views.depurar_iniciativa, name='depurar_iniciativa'),
    path('eliminar_postulacionIniciativa/<int:id>/', views.eliminarPostulacionIniciativa, name='eliminarPostulacionIniciativa'),
    path('postulacion/<int:id>/cambiar-estado_1/', views.cambiar_estado_postulacion_i, name='cambiar_estado_postulacion_i'),


    #INICIATIVAS
    path('iniciativas/', views.iniciativas, name='iniciativas'),
    path('iniciativas/ver/<int:id>/', views.verIniciativa, name='veriniciativa'),
    path('eliminar_Iniciativa/<int:id>/', views.eliminarIniciativa, name='eliminarIniciativa'),
    

    #BLOG
    path('blog/', views.posts, name='posts'),
    path('blog/crear', views.crear_post, name='crear_post'),
    path('blog/editar/<int:id>', views.editar_post, name='editar_post'),
    path('blog/eliminar_post/<int:id>', views.eliminarPost, name='eliminarPost'),
    path('blog/actualizar_masivo/', views.actualizar_check_masivo_post, name='actualizar_check_masivo_post'),

    #CONTACTO
    path('solicitudes_contacto/', views.solicitudes_contacto, name='solicitudes_contacto'),
    path('solicitudes_contacto/<int:id>', views.verSolicitud , name='ver_solicitud'),
    path('solicitudes_contacto/eliminar_post/<int:id>', views.eliminarSolicitud, name='eliminarSolicitud'),

    #GESTION EJECUTIVOS
    path('usuarios/', views.gestionar_usuarios, name='gestionar_usuarios'),
    path('usuarios/crear-ejecutivo/', views.crear_ejecutivo, name='crear_ejecutivo'),
    path('usuarios/desactivar/<int:id>/', views.desactivar_ejecutivo, name='desactivar_ejecutivo'),

]
