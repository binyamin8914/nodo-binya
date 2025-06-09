from django import template
from administracion.models import usuario_base

register = template.Library()

@register.simple_tag
def get_rol(user):
    try:
        perfil = usuario_base.objects.get(correo=user.email)
        return perfil.rol
    except usuario_base.DoesNotExist:
        return ""