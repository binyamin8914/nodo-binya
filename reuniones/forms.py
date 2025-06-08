from django import forms
from django.utils import timezone
from django.forms import DateTimeInput
from datetime import timedelta
from .models import SolicitudReunion, Reunion, ParticipanteReunion

class DateTimeLocalInput(DateTimeInput):
    input_type = "datetime-local"

class DateTimeLocalField(forms.DateTimeField):
    input_formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M"
    ]
    widget = DateTimeLocalInput(format="%Y-%m-%dT%H:%M")

class SolicitudReunionForm(forms.ModelForm):
    """Formulario para solicitar una reunión (usado por contactos)"""
    fecha_propuesta = DateTimeLocalField()
    invitados_adicionales = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'email1@ejemplo.com, email2@ejemplo.com'
        }),
        help_text="Separar correos con comas"
    )

    class Meta:
        model = SolicitudReunion
        fields = ['tipo', 'fecha_propuesta', 'duracion_propuesta', 'motivo', 'invitados_adicionales']
        widgets = {
            'motivo': forms.Textarea(attrs={'rows': 4}),
            'duracion_propuesta': forms.NumberInput(attrs={'min': 15, 'max': 240}),
            'tipo': forms.Select(),
        }
        labels = {
            'duracion_propuesta': 'Duración (minutos)'
        }

    def clean_fecha_propuesta(self):
        fecha = self.cleaned_data['fecha_propuesta']
        if fecha < timezone.now() + timedelta(minutes=30):
            raise forms.ValidationError("La reunión debe programarse con al menos 30 minutos de anticipación")
        return fecha

    def clean_duracion_propuesta(self):
        duracion = self.cleaned_data['duracion_propuesta']
        if duracion < 15:
            raise forms.ValidationError("La duración mínima es de 15 minutos")
        if duracion > 240:
            raise forms.ValidationError("La duración máxima es de 4 horas (240 minutos)")
        return duracion

class ReunionForm(forms.ModelForm):
    """Formulario para crear/editar reuniones (usado por ejecutivos)"""
    fecha = DateTimeLocalField()
    invitados_adicionales = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'email1@ejemplo.com, email2@ejemplo.com'
        }),
        help_text="Agregar invitados externos: separar correos con comas"
    )
    link_meet_manual = forms.URLField(
        required=False,
        label="Enlace de Meet manual (opcional)",
        help_text="Use este campo si no se puede generar un enlace de Google Meet automáticamente."
    )

    class Meta:
        model = Reunion
        fields = [
            'tipo',
            'fecha',
            'duracion',
            'motivo',
            'decisiones',
            'invitados_adicionales',
            'link_meet_manual'
        ]
        widgets = {
            'motivo': forms.Textarea(attrs={'rows': 4}),
            'decisiones': forms.Textarea(attrs={'rows': 3}),
            'duracion': forms.NumberInput(attrs={'min': 15, 'max': 240}),
            'tipo': forms.Select(),
        }
        labels = {
            'duracion': 'Duración (minutos)',
            'tipo': 'Tipo de reunión'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            invitados = self.instance.participantes.filter(es_invitado_externo=True)
            if invitados.exists():
                emails = ", ".join([p.email for p in invitados])
                self.fields['invitados_adicionales'].initial = emails
            if self.instance.link_meet and not self.instance.google_event_id:
                self.fields['link_meet_manual'].initial = self.instance.link_meet

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        if fecha < timezone.now() + timedelta(minutes=30):
            raise forms.ValidationError("La reunión debe programarse con al menos 30 minutos de anticipación")
        return fecha

    def clean_duracion(self):
        duracion = self.cleaned_data['duracion']
        if duracion < 15:
            raise forms.ValidationError("La duración mínima es de 15 minutos")
        if duracion > 240:
            raise forms.ValidationError("La duración máxima es de 4 horas (240 minutos)")
        return duracion

    def clean_invitados_adicionales(self):
        emails = self.cleaned_data.get('invitados_adicionales', '')
        if emails:
            email_list = [e.strip() for e in emails.split(',') if e.strip()]
            for email in email_list:
                try:
                    forms.EmailField().clean(email)
                except forms.ValidationError:
                    raise forms.ValidationError(f"'{email}' no es un email válido")
        return emails

class ResponderSolicitudForm(forms.Form):
    """Formulario para aceptar/rechazar una solicitud"""
    accion = forms.ChoiceField(
        choices=[('aceptar', 'Aceptar'), ('rechazar', 'Rechazar')],
        widget=forms.RadioSelect
    )
    fecha = DateTimeLocalField(
        label="Fecha y hora definitiva",
        help_text="Puede ajustar la fecha propuesta si es necesario"
    )
    duracion = forms.IntegerField(
        min_value=15,
        max_value=240,
        label="Duración (minutos)",
        initial=30
    )
    notas = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Notas adicionales"
    )
    link_meet_manual = forms.URLField(
        required=False,
        label="Enlace de Meet manual (opcional)",
        help_text="Use este campo si no se puede generar un enlace de Google Meet automáticamente."
    )

    def __init__(self, *args, **kwargs):
        solicitud = kwargs.pop('solicitud', None)
        super().__init__(*args, **kwargs)
        if solicitud:
            self.fields['fecha'].initial = solicitud.fecha_propuesta
            self.fields['duracion'].initial = solicitud.duracion_propuesta

class FiltroReunionesForm(forms.Form):
    """Formulario para filtrar reuniones"""
    TIPO_CHOICES = [
        ('', 'Todos'),
        ('inicial', 'Reunión Inicial'),
        ('seguimiento', 'Seguimiento'),
        ('presentacion', 'Presentación de Solución'),
        ('evaluacion', 'Evaluación'),
        ('otra', 'Otra')
    ]
    
    ESTADO_CHOICES = [
        ('', 'Todos'),
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada')
    ]
    
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        required=False,
        label="Tipo de reunión"
    )
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        label="Estado"
    )
    desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Desde"
    )
    hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Hasta"
    )

    def clean(self):
        cleaned_data = super().clean()
        desde = cleaned_data.get('desde')
        hasta = cleaned_data.get('hasta')
        if desde and hasta and desde > hasta:
            raise forms.ValidationError("La fecha 'Desde' no puede ser mayor que 'Hasta'")
        return cleaned_data