# Cristal_app/views.py
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm # Importa el formulario de creación de usuario
from django.contrib import messages # Para mostrar mensajes de éxito/error
from django.urls import reverse_lazy # Para redirigir a una URL nombrada

def home_view(request):
    context = {
        'message': '¡Bienvenido a tu panel de Cristal App con AdminLTE!',
        'items': ['Elemento 1', 'Elemento 2', 'Elemento 3']
    }
    return render(request, 'Cristal_app/home.html', context)


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'¡Cuenta creada para {username}! Ahora puedes iniciar sesión.')
            return redirect(reverse_lazy('login'))
    else:
        form = UserCreationForm()
    # ¡REVISA ESTA LÍNEA!
    return render(request, 'Cristal_app/autenticacion/templates/registration/register.html', {'form': form})
