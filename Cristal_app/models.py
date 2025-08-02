# Cristal_app/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    # Puedes añadir el campo email aquí si lo quieres en el formulario de creación de usuarios para el admin
    email = forms.EmailField(required=True, label="Email")
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Roles/Grupos"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # Asegúrate que 'groups' esté en los campos para que se muestre en el formulario de CRUD
        fields = UserCreationForm.Meta.fields + ('email', 'groups',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            if self.cleaned_data["groups"]:
                user.groups.set(self.cleaned_data["groups"])
        return user

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']