# Cristal_app/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    # Asegúrate de que 'email' y 'groups' estén bien indentados dentro de la clase
    email = forms.EmailField(required=False, label="Email") # required=True si quieres que sea obligatorio
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Roles/Grupos"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # Agrega 'email' y 'groups' a los campos existentes de UserCreationForm
        # UserCreationForm.Meta.fields ya incluye 'username', 'password', etc.
        fields = UserCreationForm.Meta.fields + ('email', 'groups',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email")
        if commit:
            user.save()
            if self.cleaned_data["groups"]: # Solo si se seleccionaron grupos
                user.groups.set(self.cleaned_data["groups"])
        return user

class CustomUserChangeForm(UserChangeForm):
    # Este campo permite editar los roles (grupos) de un usuario existente
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Roles/Grupos"
    )

    # Este campo permite editar los permisos individuales de un usuario
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Permisos de Usuario"
    )

    class Meta:
        model = User
        # Incluye todos los campos que quieres editar, incluyendo 'groups' y 'user_permissions'
        # Es mejor ser explícito aquí. Los campos básicos de UserChangeForm son 'password', 'last_login', 'is_superuser', etc.
        fields = ('username', 'email', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']