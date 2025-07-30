# Cristal/urls.py
from django.contrib import admin
from django.urls import path, include # Asegúrate de importar 'include'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Cristal_app.urls')), # Esto hará que tu home_view sea la página de inicio
    # o puedes usar: path('app/', include('Cristal_app.urls')), para acceder a ella en /app/
]