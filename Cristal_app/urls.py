
from django.urls import path
from .views import home_view

# Importar las clases de vistas directamente para usarlas en urlpatterns
from Cristal_app.views import (
    UserListView, UserCreateView, UserUpdateView, UserDeleteView,
    GroupListView, GroupCreateView, GroupUpdateView, GroupDeleteView
)

urlpatterns = [
    # Usa home_view directamente, sin 'views.'
    path('', home_view, name='home'),

    # URLs para CRUD de USUARIOS (estas ya están bien)
    path('usuarios/', UserListView.as_view(), name='user_list'), # Esta es la línea que da error
    path('usuarios/crear/', UserCreateView.as_view(), name='user_create'),
    path('usuarios/editar/<int:pk>/', UserUpdateView.as_view(), name='user_update'),
    path('usuarios/eliminar/<int:pk>/', UserDeleteView.as_view(), name='user_delete'),

    # URLs para CRUD de ROLES (Grupos) (estas ya están bien)
    path('roles/', GroupListView.as_view(), name='group_list'),
    path('roles/crear/', GroupCreateView.as_view(), name='group_create'),
    path('roles/editar/<int:pk>/', GroupUpdateView.as_view(), name='group_update'),
    path('roles/eliminar/<int:pk>/', GroupDeleteView.as_view(), name='group_delete'),
]