from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django import forms
from administracion.models import Empresa, usuario_base
from django.contrib.auth.hashers import make_password 

# Formulario personalizado para el registro
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.filter(isActive=True),
        required=False,
        empty_label="Seleccione una empresa (opcional)"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'empresa']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


# Modificar la función custom_login para manejar múltiples registros
def custom_login(request):
    if request.user.is_authenticated:
        # Redirigir según el tipo de usuario
        if request.user.is_superuser:
            return redirect('/administracion/')
        
        # Verificar si es un ejecutivo - Usar filter en lugar de get
        ejecutivo_usuarios = usuario_base.objects.filter(correo=request.user.email, rol="ejecutivo", es_activo=True)
        if ejecutivo_usuarios.exists():
            return redirect('pagina_ejecutivo')
            
        return redirect('pagina_usuario')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Redirigir según el tipo de usuario
            if user.is_superuser:
                return redirect('/administracion/')
                
            # Verificar si es un ejecutivo - Usar filter en lugar de get
            ejecutivo_usuarios = usuario_base.objects.filter(correo=user.email, rol="ejecutivo", es_activo=True)
            if ejecutivo_usuarios.exists():
                return redirect('pagina_ejecutivo')
                
            return redirect('pagina_usuario')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    return render(request, 'login.html')


# Vista para el registro - Modificar para evitar duplicados
def registro_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            empresa = form.cleaned_data.get('empresa')
            
            # Verificar si ya existe un usuario_base con este correo
            usuario_existente = usuario_base.objects.filter(correo=email).first()
            
            if not usuario_existente:
                # Crear registro en usuario_base solo si no existe
                usuario_base_obj = usuario_base.objects.create(
                    nombre=username,
                    correo=email,
                    contraseña=make_password(form.cleaned_data.get('password1')),  # Cifrar la contraseña
                    rol="usuario_externo",
                    es_activo=True,
                    cargo="Usuario Externo",
                    telefono="",
                    empresa=empresa
                )
            else:
                # Actualizar el usuario existente si es necesario
                usuario_existente.nombre = username
                usuario_existente.es_activo = True
                if empresa:
                    usuario_existente.empresa = empresa
                usuario_existente.save()
            
            messages.success(request, f'Cuenta creada para {username}! Ahora puedes iniciar sesión.')
            return redirect('login')
        else:
            # El formulario no es válido, pasamos el formulario con errores al template
            return render(request, 'registro.html', {'form': form})
    else:
        form = CustomUserCreationForm()
    return render(request, 'registro.html', {'form': form})


# Vista para el logout
def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


# Para redirigir segun el usuario - Modificar para usar filter
@login_required
def pagina_usuario(request):
    if request.user.is_superuser:
        return redirect('/administracion/') 
    return render(request, 'usuario_basico.html')

# Modificar esta vista para usar filter
@login_required
def pagina_ejecutivo(request):
    # Verificar si el usuario es un ejecutivo usando filter
    ejecutivo_usuarios = usuario_base.objects.filter(correo=request.user.email, rol="ejecutivo", es_activo=True)
    if not ejecutivo_usuarios.exists():
        return redirect('pagina_usuario')
        
    return render(request, 'ejecutivo.html')


# Vista para cambiar la contraseña - Modificar para redirigir según el rol
@login_required
def cambiar_password(request):
    # Determinar el rol del usuario
    es_ejecutivo = usuario_base.objects.filter(correo=request.user.email, rol="ejecutivo", es_activo=True).exists()
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Importante para mantener la sesión activa
            
            # Actualizar también la contraseña en usuario_base si existe - Usar filter
            usuarios = usuario_base.objects.filter(correo=request.user.email)
            for usuario in usuarios:
                # Cifrar la nueva contraseña antes de guardarla
                usuario.contraseña = make_password(form.cleaned_data.get('new_password1'))  # Cifra la nueva contraseña
                usuario.save()
            
            messages.success(request, 'Tu contraseña ha sido actualizada correctamente!')
            
            # Redirigir según el rol del usuario
            if es_ejecutivo:
                return redirect('pagina_ejecutivo')
            else:
                return redirect('pagina_usuario')
        else:
            messages.error(request, 'Por favor corrige los errores.')
    else:
        form = PasswordChangeForm(request.user)
    
    # Pasar el rol del usuario a la plantilla
    return render(request, 'cambiar_password.html', {
        'form': form,
        'es_ejecutivo': es_ejecutivo
    })
