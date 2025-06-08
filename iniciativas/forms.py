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



class PostulacionIniciativaForm(forms.Form):
    TRACCION_CHOICES = [
        ("Prototipo en desarrollo ", "Prototipo en desarrollo "),
        ("Prototipo con piloto ", "Prototipo con piloto"),
        ("Ingresos menores a US$100.000", "Producto en el mercado"),
        ("Ingresos entre US$100.000 - US$300.000", "Ingresos entre US$100.000 - US$300.000"),
        ("Ingresos entre US$100.000 - US$300.000", "Ingresos entre US$100.000 - US$300.000"),
        ("Ingresos entre US$300.000 - US$600.000", "Ingresos entre US$300.000 - US$600.000"),
        ("Ingresos entre US$600.000 - US$1.000.000", "Ingresos entre US$600.000 - US$1.000.000"),
        ("Ingresos entre US$1.000.000 - US$2.000.000", "Ingresos entre US$1.000.000 - US$2.000.000"),
        ("Ingresos sobre US$2.000.000 ", "Ingresos sobre US$2.000.000 "),
    ]

    titulo = forms.CharField(max_length=255)
    descripcion = forms.CharField(widget=forms.Textarea)
    pregunta = forms.CharField(max_length=255)
    origen = forms.CharField(max_length=255)
    latam = forms.ChoiceField(choices=[('Si','Si'), ('No','No'),])
    video = forms.URLField(max_length=255 , required=False)
    diferenciacion = forms.CharField(widget=forms.Textarea)
    traccion = forms.ChoiceField(choices=TRACCION_CHOICES)
    piloto = forms.CharField(widget=forms.Textarea)
    captcha = CaptchaField()

