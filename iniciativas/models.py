from django.db import models
from django.contrib.auth.models import User
from desafios.models import Desafio
from administracion.models import Empresa, usuario_base
# Create your models here.
class PostulacionIniciativa(models.Model):
    
    id = models.AutoField(primary_key=True)  
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    contacto = models.ForeignKey(usuario_base, on_delete=models.CASCADE)

    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    pregunta = models.CharField(max_length=255)
    origen = models.CharField(max_length=255)
    latam = models.CharField(max_length=255)
    video = models.URLField(max_length=255, blank=True)    
    diferenciacion = models.TextField(max_length=255)
    traccion = models.TextField(max_length=255)
    piloto = models.TextField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)
    desafio = models.ForeignKey(
        Desafio, on_delete=models.SET_NULL, null=True, blank=True
    )
    isActive = models.BooleanField(default=True)
    estado = models.CharField(max_length=255, default="Por Depurar")
    def __str__(self):
        return self.titulo
    

class Iniciativa(models.Model):
    id = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=255)  
    descripcion = models.TextField()
    preevaluacion = models.TextField()
    recomendacion = models.TextField()
    madurez = models.CharField(max_length=255)
    presentacion = models.FileField(blank=True)
    comite= models.CharField(max_length=255)
    
    fecha = models.DateTimeField(auto_now_add=True)
    
    postulacion = models.ForeignKey(PostulacionIniciativa, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    contacto= models.ForeignKey(usuario_base, on_delete=models.CASCADE)
    ejecutivo = models.ForeignKey(User, on_delete=models.CASCADE)
    desafio= models.ForeignKey(Desafio, on_delete=models.CASCADE)
    isActive = models.BooleanField(default=True)
    def __str__(self):
        return self.titulo