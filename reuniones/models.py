from django.db import models
from django.utils import timezone
from administracion.models import Match, usuario_base
from datetime import timedelta
from datetime import datetime

class GoogleToken(models.Model):
    user = models.OneToOneField(usuario_base, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True)
    token_uri = models.CharField(max_length=200)
    client_id = models.CharField(max_length=200)
    client_secret = models.CharField(max_length=200)
    scopes = models.TextField()
    expiry = models.DateTimeField(null=True)
    
    def is_expired(self):
        if not self.expiry:
            return True
        # Convertir la fecha de expiración a tipo aware si es naive
        expiry = self.expiry
        if expiry.tzinfo is None:
            import pytz
            from django.conf import settings
            timezone = pytz.timezone(settings.TIME_ZONE)
            expiry = timezone.localize(expiry)
        
        # Obtener la hora actual con zona horaria
        now = timezone.now()
        
        # Comparar fechas aware
        return expiry <= now
    
    def __str__(self):
        return f"Token de Google para {self.user.nombres}"

class SolicitudReunion(models.Model):
    """
    Solicitudes de reunión entre participantes de un match
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada')
    ]
    TIPO_CHOICES = [
        ('inicial', 'Reunión Inicial'),
        ('seguimiento', 'Seguimiento'),
        ('presentacion', 'Presentación de Solución'),
        ('evaluacion', 'Evaluación'),
        ('otra', 'Otra')
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='solicitudes_reunion', verbose_name='Match relacionado')
    solicitante = models.ForeignKey(usuario_base, on_delete=models.CASCADE, related_name='solicitudes_enviadas', verbose_name='Usuario que solicita')
    destinatario = models.ForeignKey(usuario_base, on_delete=models.CASCADE, related_name='solicitudes_recibidas', verbose_name='Usuario destinatario')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='inicial', verbose_name='Tipo de reunión')
    fecha_propuesta = models.DateTimeField(verbose_name='Fecha y hora propuesta')
    duracion_propuesta = models.PositiveIntegerField(default=30, verbose_name='Duración propuesta (minutos)')
    motivo = models.TextField(verbose_name='Motivo de la reunión')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado de la solicitud')
    invitados_adicionales = models.TextField(blank=True, verbose_name='Invitados adicionales', help_text='Correos electrónicos separados por comas')
    creada_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    actualizada_en = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = 'Solicitud de Reunión'
        verbose_name_plural = 'Solicitudes de Reunión'
        ordering = ['-creada_en']
        permissions = [
            ('puede_solicitar', 'Puede solicitar reuniones'),
            ('puede_responder', 'Puede responder a solicitudes'),
        ]

    def __str__(self):
        return f"Solicitud #{self.id} - {self.get_tipo_display()} para {self.match}"

    def get_participantes_base(self):
        """Devuelve los usuarios que deben participar por defecto"""
        return [self.match.ejecutivo, self.match.desafio.contacto]  # Ajusta si contacto no es usuario_base

class Reunion(models.Model):
    """
    Reuniones agendadas en el sistema
    """
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='reuniones', verbose_name='Match relacionado')
    organizador = models.ForeignKey(usuario_base, on_delete=models.CASCADE, related_name='reuniones_organizadas', verbose_name='Ejecutivo organizador', limit_choices_to={'rol': 'ejecutivo'})
    solicitud_origen = models.OneToOneField(SolicitudReunion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Solicitud origen')
    tipo = models.CharField(max_length=20, choices=SolicitudReunion.TIPO_CHOICES, default='inicial', verbose_name='Tipo de reunión')
    fecha = models.DateTimeField(verbose_name='Fecha y hora')
    duracion = models.PositiveIntegerField(verbose_name='Duración (minutos)', help_text='Duración en minutos')
    motivo = models.TextField(verbose_name='Motivo de la reunión')
    decisiones = models.TextField(blank=True, verbose_name='Decisiones tomadas')
    link_meet = models.URLField(blank=True, null=True, verbose_name='Enlace Meet')
    google_event_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='ID Evento Google')
    creada_en = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    actualizada_en = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        verbose_name = 'Reunión'
        verbose_name_plural = 'Reuniones'
        ordering = ['-fecha']
        permissions = [
            ('puede_agendar', 'Puede agendar reuniones'),
            ('puede_invitar_externos', 'Puede invitar participantes externos'),
        ]

    def __str__(self):
        return f"Reunión #{self.id} - {self.get_tipo_display()} - {self.match}"

    @property
    def fin(self):
        """Calcula la fecha/hora de finalización"""
        return self.fecha + timedelta(minutes=self.duracion)

    def crear_evento_google(self):
        """Crea el evento en Google Calendar"""
        import logging
        logger = logging.getLogger(__name__)
        
        if not hasattr(self.organizador, 'googletoken'):
            logger.error(f"Reunión {self.id}: El organizador no tiene token de Google")
            return None
            
        from .google_api import crear_evento_oauth
        try:
            event_id, meet_link = crear_evento_oauth(self.organizador, self)
            self.google_event_id = event_id
            self.link_meet = meet_link
            self.save()
            logger.info(f"Evento creado exitosamente para reunión {self.id}: {meet_link}")
            return True
        except Exception as e:
            logger.error(f"Reunión {self.id}: Error al crear evento en Google: {str(e)}")
            # Registramos el error completo para diagnóstico
            import traceback
            logger.error(traceback.format_exc())
            return False

class ParticipanteReunion(models.Model):
    """
    Participantes en una reunión (usuarios internos o invitados externos)
    """
    reunion = models.ForeignKey(Reunion, on_delete=models.CASCADE, related_name='participantes', verbose_name='Reunión')
    usuario = models.ForeignKey(usuario_base, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Usuario registrado')
    email = models.EmailField(verbose_name='Correo electrónico')
    nombre = models.CharField(max_length=255, blank=True, verbose_name='Nombre completo')
    asistio = models.BooleanField(default=False, verbose_name='Confirmó asistencia')
    es_invitado_externo = models.BooleanField(default=False, verbose_name='Es invitado externo?')
    notificado = models.BooleanField(default=False, verbose_name='Fue notificado?')

    class Meta:
        verbose_name = 'Participante de Reunión'
        verbose_name_plural = 'Participantes de Reuniones'
        unique_together = ('reunion', 'email')
        ordering = ['-es_invitado_externo', 'nombre']

    def __str__(self):
        return f"{self.nombre or self.email} - {'Asistió' if self.asistio else 'No asistió'}"

    def save(self, *args, **kwargs):
        # Autocompletar nombre si es usuario registrado
        if self.usuario and not self.nombre:
            self.nombre = self.usuario.nombre  # usuario_base tiene campo 'nombre'
        super().save(*args, **kwargs)