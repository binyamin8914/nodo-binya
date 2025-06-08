from django.shortcuts import redirect
from django.conf import settings
from django.contrib import messages
from administracion.models import usuario_base
from django_tenants.utils import get_tenant

class RestrictAppMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = get_tenant(request)
        schema_name = tenant.schema_name if tenant else 'public'

        if not request.user.is_authenticated:
            if request.path.startswith(('/autenticacion/usuario/', '/autenticacion/ejecutivo/', f'/{schema_name}/administracion/', f'/{schema_name}/reuniones/')):
                return redirect(f'/{schema_name}{settings.LOGIN_URL}')
            return self.get_response(request)

        if request.user.is_superuser:
            return self.get_response(request)

        try:
            user_base = usuario_base.objects.get(correo=request.user.email)
            is_ejecutivo = request.user.is_staff and user_base.rol == "ejecutivo"

            if request.path.startswith(f'/{schema_name}/administracion/'):
                if not is_ejecutivo:
                    messages.error(request, "No tienes permiso para acceder a esta sección.")
                    return redirect(f'/{schema_name}{settings.LOGIN_REDIRECT_URL}')

            elif request.path.startswith(f'/{schema_name}/reuniones/'):
                if not (is_ejecutivo or user_base.rol == "contacto"):
                    messages.error(request, "No tienes permiso para acceder a esta sección.")
                    return redirect(f'/{schema_name}{settings.LOGIN_REDIRECT_URL}')

            elif request.path.startswith(f'/{schema_name}/autenticacion/ejecutivo/'):
                if not is_ejecutivo:
                    messages.error(request, "Solo los ejecutivos pueden acceder a esta sección.")
                    return redirect(f'/{schema_name}/autenticacion/usuario/')

            elif request.path.startswith(f'/{schema_name}/autenticacion/usuario/'):
                if is_ejecutivo:
                    messages.error(request, "Los ejecutivos no pueden acceder a esta sección.")
                    return redirect(f'/{schema_name}/autenticacion/ejecutivo/')

            return self.get_response(request)
        except usuario_base.DoesNotExist:
            messages.error(request, "No se encontró un registro de usuario asociado. Contacta al administrador.")
            return redirect(f'/{schema_name}{settings.LOGIN_REDIRECT_URL}')
        except usuario_base.MultipleObjectsReturned:
            messages.error(request, "Se encontraron múltiples registros con este correo. Contacta al administrador.")
            return redirect(f'/{schema_name}{settings.LOGIN_REDIRECT_URL}')