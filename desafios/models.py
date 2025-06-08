from django.db import models
from django.contrib.auth.models import User
from administracion.models import Empresa, usuario_base
from storages.backends.s3boto3 import S3Boto3Storage
import os

class PostulacionDesafio (models.Model):
    id = models.AutoField(primary_key=True)  
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    contacto = models.ForeignKey(usuario_base, on_delete=models.CASCADE)
    
    fecha = models.DateTimeField(auto_now_add=True)  
    descripcionInicial = models.TextField()  
    desafioFrase = models.TextField()  
    presupuesto = models.CharField(max_length=255) 
    pregunta = models.TextField()   #preguntas sobre NODO
    origen = models.CharField(max_length=255)  #como te enteraste de NODO
    estado = models.CharField(default="Por Depurar") #Depurado, Descartado, Por depurar
    
    isActive = models.BooleanField(default=True)
    def __str__(self):
        return "Postulacion "+ str(self.id)

class Desafio (models.Model):   
    id = models.AutoField(primary_key=True)  
    postulacion = models.ForeignKey(PostulacionDesafio, on_delete=models.CASCADE)  
    ejecutivo = models.ForeignKey(User, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    contacto = models.ForeignKey(usuario_base, on_delete=models.CASCADE)

    fecha = models.DateTimeField(auto_now_add=True)  

    webEmpresa = models.URLField(max_length=255,blank=True)  # URL del sitio web de la empresa
    nombreDesafio = models.CharField(max_length=255,blank=False)  
    impactoProblema = models.TextField(blank=True)  
    efectoOperacion = models.TextField(blank=True)  
    descripcionDesafio = models.TextField(blank=True)

    costoOportunidad = models.DecimalField(max_digits=15, decimal_places=2,blank=True)  
    intentosPreviosSolucion = models.TextField(blank=True)  
    ventasMesUsd = models.DecimalField(max_digits=15, decimal_places=2,null=True)  
    margenBruto = models.DecimalField(max_digits=15, decimal_places=2,null=True)  
    ebitda = models.DecimalField(max_digits=15, decimal_places=2,null=True)  
    cantidadClientes = models.IntegerField(null=True)  

    imagen = models.ImageField(upload_to='Desafios/', blank=False, null=False, default='Desafios/default.jpg')
    isPrincipal = models.BooleanField(default=False)
    show = models.BooleanField(default=False)
    
    isActive = models.BooleanField(default=True)
    def __str__(self):
        return self.nombreDesafio