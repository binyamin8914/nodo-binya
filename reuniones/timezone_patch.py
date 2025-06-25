# timezone_patch.py
import datetime
import logging
import functools
from django.utils import timezone
import pytz

logger = logging.getLogger(__name__)

# Guardar las funciones originales
_original_eq = datetime.__eq__
_original_lt = datetime.__lt__
_original_gt = datetime.__gt__
_original_le = datetime.__le__
_original_ge = datetime.__ge__

def safe_datetime_compare(func):
    """
    Decorator que hace seguras las comparaciones de datetime
    """
    @functools.wraps(func)
    def wrapper(self, other):
        if not isinstance(other, datetime):
            return NotImplemented
            
        # Si ambos tienen timezone o ambos no tienen, usar comparación normal
        if (self.tzinfo is None and other.tzinfo is None) or (self.tzinfo is not None and other.tzinfo is not None):
            return func(self, other)
            
        # Si uno tiene timezone y el otro no, hacer ambos aware
        try:
            # Determinar cuál es naive y hacer aware
            if self.tzinfo is None:
                self_aware = timezone.make_aware(self)
                other_aware = other
            else:
                self_aware = self
                other_aware = timezone.make_aware(other)
                
            # Escribir log para diagnóstico
            logger.warning(f"Corrigiendo comparación de fechas naive/aware: {self} vs {other}")
            
            # Ejecutar la comparación con ambos aware
            return func(self_aware, other_aware)
        except Exception as e:
            logger.error(f"Error en comparación segura: {e}")
            return NotImplemented
            
    return wrapper

# Reemplazar los métodos de comparación con versiones seguras
def apply_patch():
    datetime.__eq__ = safe_datetime_compare(_original_eq)
    datetime.__lt__ = safe_datetime_compare(_original_lt)
    datetime.__gt__ = safe_datetime_compare(_original_gt)
    datetime.__le__ = safe_datetime_compare(_original_le)
    datetime.__ge__ = safe_datetime_compare(_original_ge)
    logger.info("Parche de seguridad para comparaciones datetime aplicado")

def remove_patch():
    datetime.__eq__ = _original_eq
    datetime.__lt__ = _original_lt
    datetime.__gt__ = _original_gt
    datetime.__le__ = _original_le
    datetime.__ge__ = _original_ge
    logger.info("Parche de seguridad para comparaciones datetime removido")