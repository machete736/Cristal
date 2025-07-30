# Cristal_app/views.py
from django.shortcuts import render

def home_view(request):
    context = {
        'message': '¡Bienvenido a tu panel de Cristal App con AdminLTE!',
        'items': ['Elemento 1', 'Elemento 2', 'Elemento 3']
    }
    return render(request, 'Cristal_app/home.html', context)