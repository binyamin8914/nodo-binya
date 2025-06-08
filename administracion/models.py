from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.module_loading import import_string
from django.contrib.auth.models import User
from django.apps import apps
import uuid
import os

def get_desafio():
    return apps.get_model('desafios', 'Desafio')

def get_iniciativa():
    return apps.get_model('iniciativas', 'Iniciativa')

StorageClass = import_string(settings.STORAGES['private_files']["BACKEND"])


def document_upload_path(instance, filename):
    # extensión del archivo
    ext = filename.split('.')[-1]
    # nombre único
    unique_name = f"{uuid.uuid4()}.{ext}"
    # ruta dentro de MEDIA_ROOT
    return os.path.join("documentos", unique_name)


class Documento(models.Model):
    archivo = models.FileField(
        upload_to=document_upload_path ,
        storage=StorageClass(location=settings.STORAGES['private_files']["OPTIONS"]["location"]),  # 🔒 Se almacena de forma privada
    )
    nombre = models.CharField(max_length=255)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    # Relación genérica
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)  # Tipo de objeto relacionado
    object_id = models.PositiveIntegerField()  # ID del objeto relacionado
    content_object = GenericForeignKey('content_type', 'object_id')  # Relación genérica

    def __str__(self):
        return f"{self.nombre} - Relacionado con ID {self.object_id} ({self.content_type})"

# Create your models here.
class Empresa (models.Model):   
    id=models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    cantPersonas = models.IntegerField()
    año = models.IntegerField()
    actividad = models.CharField(max_length=255)
    pais = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=255)
    isActive = models.BooleanField(default=True)
    def __str__(self):
        return self.nombre

class usuario_base(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    correo = models.CharField(max_length=255)
    contraseña = models.EmailField()
    rol = models.CharField(max_length=100)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    es_activo = models.BooleanField(default=True)
    cargo = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    empresa = models.ForeignKey('Empresa', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = 'Usuario Base'
        verbose_name_plural = 'Usuarios Base'
    

class solicitudContacto (models.Model):
    id=models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    cargo = models.CharField(max_length=255)
    correo = models.EmailField(max_length=255)
    telefono = models.CharField(max_length=20)
    empresa = models.CharField(max_length=255)
    pais = models.CharField(max_length=255)
    mensaje = models.TextField()
    origen = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)
    isActive = models.BooleanField(default=True)
    def __str__(self):
        return self.nombre
    

class Match (models.Model):
    id=models.AutoField(primary_key=True)
    estado = models.CharField(max_length=255)
    brl = models.CharField(max_length=255)
    trl = models.CharField(max_length=255)
    ejecutivo = models.ForeignKey(User, on_delete=models.CASCADE)
    desafio = models.ForeignKey('desafios.Desafio', on_delete=models.CASCADE)
    iniciativa = models.ForeignKey('iniciativas.Iniciativa', on_delete=models.CASCADE)

    isActive = models.BooleanField(default=True)
    def __str__(self):
        return self.id
    
class Objetivo (models.Model):
    id=models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    responsable = models.CharField(max_length=255)
    fechaObjetivo = models.DateTimeField()
    perspectiva = models.CharField(max_length=255)

    fecha = models.DateTimeField(auto_now_add=True)
    isActive = models.BooleanField(default=True)

    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    def __str__(self):
        return self.nombre
    
class Metrica (models.Model):
    id=models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    valorInicial = models.IntegerField()
    valorDeseado = models.IntegerField()
    periodo = models.CharField(max_length=255)

    fecha = models.DateTimeField(auto_now_add=True)
    isActive = models.BooleanField(default=True)

    objetivo = models.ForeignKey(Objetivo, on_delete=models.CASCADE)
    def __str__(self):
        return self.nombre
    
class Evaluacion (models.Model):
    id=models.AutoField(primary_key=True)
    valor = models.IntegerField()   
    nota = models.TextField()

    fecha = models.DateTimeField()

    isActive = models.BooleanField(default=True)

    metrica = models.ForeignKey(Metrica, on_delete=models.CASCADE)
    def __str__(self):
        return self.nombre
    
class Actividad (models.Model):
    id=models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    fechaCreacion = models.DateTimeField( auto_now_add=True)
    fechaRealizado = models.DateTimeField( blank=True, null=True)
    estado= models.CharField(max_length=255)
    responsable = models.CharField(max_length=255)

    isActive = models.BooleanField(default=True)

    metrica = models.ForeignKey(Metrica, on_delete=models.CASCADE)
    def __str__(self):
        return self.nombre  