from django.conf import settings
from django.utils import timezone
import pytz
from datetime import datetime, timedelta
import base64

def ensure_aware(dt):
    """
    Asegura que un datetime tenga información de zona horaria.
    Si no la tiene, se le asigna la zona horaria definida en settings.TIME_ZONE.
    """
    if dt is None:
        return None
        
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            tz = pytz.timezone(settings.TIME_ZONE)
            return tz.localize(dt)
    return dt

def get_now_aware():
    """
    Retorna la fecha y hora actual con zona horaria.
    Siempre usar esta función en lugar de datetime.now() o timezone.now()
    """
    return timezone.now()

def compare_dates_safely(date1, date2):
    """
    Compara dos fechas de manera segura, asegurándose de que ambas tengan zona horaria.
    """
    return ensure_aware(date1) < ensure_aware(date2)

def is_future_date(check_date):
    """
    Verifica si una fecha está en el futuro, manejando zonas horarias.
    """
    now = get_now_aware()
    check_date = ensure_aware(check_date)
    return check_date > now

def encode_google_calendar_id(event_id):
    """
    Codifica el ID del evento para usarlo en URLs de Google Calendar.
    Google Calendar espera un formato específico, no solo base64 simple.
    """
    if not event_id:
        return ""
    
    # Para eventos de Google Calendar, no necesitamos codificar el ID
    # Solo necesitamos construir la URL correcta
    return event_id

def puede_unirse_reunion(reunion):
    """
    Determina si ya es momento de unirse a una reunión (30 minutos antes).
    """
    ahora = timezone.now()
    inicio = ensure_aware(reunion.fecha)
    tiempo_permitido = inicio - timedelta(minutes=30)  # 30 minutos antes
    
    return ahora >= tiempo_permitido

def tiempo_restante_reunion(reunion):
    """
    Calcula el tiempo restante para poder unirse a una reunión.
    Devuelve un string formateado o None si ya es posible unirse.
    """
    ahora = timezone.now()
    inicio = ensure_aware(reunion.fecha)
    tiempo_permitido = inicio - timedelta(minutes=30)
    
    if ahora >= tiempo_permitido:
        return None
        
    segundos_restantes = (tiempo_permitido - ahora).total_seconds()
    horas = int(segundos_restantes // 3600)
    minutos = int((segundos_restantes % 3600) // 60)
    
    if horas > 0:
        return f"{horas}h {minutos}min"
    else:
        return f"{minutos} minutos"