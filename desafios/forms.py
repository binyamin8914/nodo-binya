from django import forms
from captcha.fields import CaptchaField
from django import forms

class EmpresaForm(forms.Form):
    nombre = forms.CharField(max_length=255)
    cantPersonas = forms.IntegerField()
    año = forms.IntegerField()
    actividad = forms.CharField(max_length=255)
    pais = forms.CharField(max_length=255)
    ciudad = forms.CharField(max_length=255)

class ContactoEmpresaForm(forms.Form):
    nombre = forms.CharField(max_length=255)
    cargo = forms.CharField(max_length=255)
    correo = forms.EmailField(max_length=255)
    telefono = forms.CharField(max_length=20)

class PostulacionDesafioForm(forms.Form):
    descripcionInicial = forms.CharField(widget=forms.Textarea)
    desafioFrase = forms.CharField(max_length=255)
    presupuesto = forms.ChoiceField(choices=[('si', 'Sí'), ('no', 'No')], widget=forms.Select)

    pregunta = forms.CharField(max_length=255)
    origen = forms.CharField(max_length=255)
    captcha = CaptchaField()
