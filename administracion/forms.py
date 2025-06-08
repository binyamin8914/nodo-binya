from django import forms
from desafios.models import Desafio
from iniciativas.models import Iniciativa
from django_summernote.widgets import SummernoteWidget
from blog.models import Post
from django.utils.text import slugify
from .models import solicitudContacto, Match, Objetivo, Metrica, Evaluacion, Actividad
#extensiones sprint 1
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class DesafioForm(forms.ModelForm):
    documentos = forms.FileField(
        widget=forms.ClearableFileInput(),
        required=False,
        label="Documentos"
    )

    class Meta:
        model = Desafio
        
        fields = [
            'webEmpresa', 'nombreDesafio', 'impactoProblema', 'efectoOperacion',
            'descripcionDesafio', 'costoOportunidad', 'intentosPreviosSolucion',
            'ventasMesUsd', 'margenBruto', 'ebitda',
            'cantidadClientes', 'imagen', 'isPrincipal', 'show'
        ]
        widgets = {
            'fecha': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'imagen': forms.ClearableFileInput(attrs={'multiple': False}),
            'postulacion': forms.Select(attrs={'disabled': 'disabled'}),
            'contacto': forms.Select(attrs={'disabled': 'disabled'}),
        }
class DesafioBulkUpdateForm(forms.Form):
    desafios = forms.ModelMultipleChoiceField(queryset=Desafio.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['titulo','autor','portada','contenido','tags','slug']
        widgets = {
            'portada': forms.ClearableFileInput(attrs={'class': 'custom-file-input'}),
            'contenido': SummernoteWidget(),
            'tags': forms.TextInput(attrs={'placeholder': 'Ejemplo: Innovacion, Chile, Tecnologia'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class ContactoForm(forms.ModelForm):
    class Meta:
        model = solicitudContacto
        fields = ['nombre','cargo','correo','telefono','empresa','pais','mensaje', 'origen']
        widgets = {
            'mensaje': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Escriba aquí su mensaje'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)



class IniciativaForm(forms.ModelForm):
    documentos = forms.FileField(
        widget=forms.ClearableFileInput(),
        required=False,
        label="Documentos"
    )

    class Meta:
        model = Iniciativa
        
        fields = [
            'titulo',
            'descripcion', 'preevaluacion', 'recomendacion', 'madurez',
            'presentacion', 'comite','desafio',
        ]
        widgets = {
            'presentacion': forms.ClearableFileInput(attrs={'multiple': False}),
            'desafio': forms.Select(),
        }


class  MatchForm (forms.ModelForm):
    class Meta:
        model = Match
        fields = ['estado', 'ejecutivo', 'desafio', 'iniciativa','brl','trl']
        widgets = {
            'estado': forms.Select(choices=[('','Selecciona un estado'),
                                            ('Pendiente', 'Pendiente'),
                                            ('En Proceso', 'En Proceso'),
                                            ('Finalizado', 'Finalizado')]),  
            'brl': forms.Select(choices=[('','Selecciona una opcion'),
                                           ('BRL 1', 'BRL 1'),
                                           ('BRL 2', 'BRL 2'),
                                           ('BRL 3', 'BRL 3'),
                                           ('BRL 4', 'BRL 4'),
                                           ('BRL 5', 'BRL 5'),
                                           ('BRL 6', 'BRL 6'),
                                           ('BRL 7', 'BRL 7'),
                                           ('BRL 8', 'BRL 8'),
                                           ('BRL 9', 'BRL 9')]  ),
            'trl': forms.Select(choices=[('','Selecciona una opcion'),
                                           ('TRL 1', 'TRL 1'),
                                           ('TRL 2', 'TRL 2'),
                                           ('TRL 3', 'TRL 3'),
                                           ('TRL 4', 'TRL 4'),
                                           ('TRL 5', 'TRL 5'),
                                           ('TRL 6', 'TRL 6'),
                                           ('TRL 7', 'TRL 7'),
                                           ('TRL 8', 'TRL 8'),
                                           ('TRL 9', 'TRL 9')]  ),
            
        }
        def __init__(self, *args, **kwargs):
            user = kwargs.pop('user', None)  # Obtén el usuario actual desde la vista
            super().__init__(*args, **kwargs)
            if user:
                self.fields['ejecutivo'].queryset = Iniciativa.objects.filter(ejecutivo=user)
                self.fields['ejecutivo'].initial = user.id



class ObjetivoForm(forms.ModelForm):
    class Meta:
        model = Objetivo
        fields = ['nombre', 'responsable', 'fechaObjetivo', 'perspectiva']
        widgets ={
            'perspectiva': forms.Select(choices=[('','Selecciona una perspectiva'),
                                            ('Financiera', 'Financiera'),
                                            ('De  cliente', 'De  cliente'),
                                            ('Procesos y operaciones', 'Procesos y operaciones'),
                                            ('Personas', 'Personas')]),  
            'fechaObjetivo': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class MetricaForm(forms.ModelForm): 
    class Meta:
        model = Metrica
        fields = ['nombre', 'valorInicial', 'valorDeseado', 'periodo']
        widgets = {
            'periodo': forms.Select(choices=[('','Selecciona un periodo'),
                                            ('Diario', 'Diario'),
                                            ('Semanal', 'Semanal'),
                                            ('Mensual', 'Mensual'),
                                            ('Semestral', 'Semestral'),
                                            ('Anual', 'Anual')]),  
        }

class EvaluacionForm(forms.ModelForm):
    class Meta:
        model = Evaluacion 
        fields = [ 'valor', 'nota','fecha']
        widgets = {

            'nota': forms.Textarea(attrs={'placeholder': 'Escriba aquí su nota'}),
            'fecha': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad   
        fields = ['nombre', 'descripcion', 'fechaRealizado','estado','responsable']
        widgets = {
            'fechaRealizado': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'estado': forms.Select(choices=[('','Selecciona un estado'),
                                            ('Pendiente', 'Pendiente'),
                                            ('En Proceso', 'En Proceso'),
                                            ('Finalizado', 'Finalizado')]),
        }
        

class EjecutivoCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    nombre_completo = forms.CharField(max_length=255, required=True, label="Nombre completo")
    telefono = forms.CharField(max_length=20, required=False, label="Teléfono")
    cargo = forms.CharField(max_length=255, required=True, label="Cargo")
    
    class Meta:
        model = User
        fields = ['username', 'email', 'nombre_completo', 'telefono', 'cargo', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_staff = True  # Los ejecutivos tienen acceso al panel de administración
        if commit:
            user.save()
        return user