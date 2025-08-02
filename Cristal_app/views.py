from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator # <-- ADD THIS IMPORT

from .forms import CustomUserCreationForm, CustomUserChangeForm, GroupForm

User = get_user_model()

# This is a function-based view, so the decorator is correct.
@login_required
def home_view(request):
    context = {
        'message': '¡Bienvenido a tu panel de Cristal App con AdminLTE!',
        'items': ['Elemento 1', 'Elemento 2', 'Elemento 3']
    }
    return render(request, 'Cristal_app/home.html', context)

# --- Vistas para CRUD de USUARIOS (CORRECTED) ---

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('auth.view_user', raise_exception=True), name='dispatch')
class UserListView(ListView):
    model = User
    template_name = 'Cristal_app/Acceso/usuarios/user_list.html'
    context_object_name = 'users'

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('auth.add_user', raise_exception=True), name='dispatch')
class UserCreateView(SuccessMessageMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'Cristal_app/Acceso/usuarios/user_form.html'
    success_url = reverse_lazy('user_list')
    success_message = "Usuario '%(username)s' creado exitosamente."
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Crear'
        return context

# ... Continue this pattern for all other class-based views ...

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('auth.change_user', raise_exception=True), name='dispatch')
class UserUpdateView(SuccessMessageMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'Cristal_app/Acceso/usuarios/user_form.html'
    context_object_name = 'user'
    success_url = reverse_lazy('user_list')
    success_message = "Usuario '%(username)s' actualizado exitosamente."
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Editar'
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('auth.delete_user', raise_exception=True), name='dispatch')
class UserDeleteView(SuccessMessageMixin, DeleteView):
    model = User
    template_name = 'Cristal_app/Acceso/usuarios/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')
    context_object_name = 'user'
    success_message = "Usuario '%(username)s' eliminado exitosamente."
    def form_valid(self, form):
        messages.success(self.request, self.success_message % {'username': self.object.username})
        return super().form_valid(form)

# --- Vistas para CRUD de ROLES (Grupos) (CORRECTED) ---

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('auth.view_group', raise_exception=True), name='dispatch')
class GroupListView(ListView):
    model = Group
    template_name = 'Cristal_app/Acceso/roles/group_list.html'
    context_object_name = 'groups'

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('auth.add_group', raise_exception=True), name='dispatch')
class GroupCreateView(SuccessMessageMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'Cristal_app/Acceso/roles/group_form.html'
    success_url = reverse_lazy('group_list')
    success_message = "Rol '%(name)s' creado exitosamente."
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Crear'
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('auth.change_group', raise_exception=True), name='dispatch')
class GroupUpdateView(SuccessMessageMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'Cristal_app/Acceso/roles/group_form.html'
    context_object_name = 'group'
    success_url = reverse_lazy('group_list')
    success_message = "Rol '%(name)s' actualizado exitosamente."
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Editar'
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('auth.delete_group', raise_exception=True), name='dispatch')
class GroupDeleteView(SuccessMessageMixin, DeleteView):
    model = Group
    template_name = 'Cristal_app/Acceso/roles/group_confirm_delete.html'
    success_url = reverse_lazy('group_list')
    context_object_name = 'group'
    success_message = "Rol '%(name)s' eliminado exitosamente."
    def form_valid(self, form):
        messages.success(self.request, self.success_message % {'name': self.object.name})
        return super().form_valid(form)