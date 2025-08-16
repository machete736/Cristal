# Cristal_app/forms.py

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from decimal import Decimal
from django import forms
from django.forms import inlineformset_factory, SplitDateTimeWidget
from django.utils import timezone

# Importaciones de modelos (Corregidas: sin duplicados)
from .models import (
    Compra, DetalleCompra, Venta, DetalleVenta, Producto, Cliente, Proveedor,
    Categoria, Reserva, Pago, Acompanante, Tarifa, Habitacion, TipoPago
)

# Obtiene el modelo de usuario activo
User = get_user_model()


# --- FORMULARIOS DE ACCESO (USUARIOS Y GRUPOS) ---

class CustomUserCreationForm(UserCreationForm):
    """
    Formulario para la creación de un nuevo usuario, extendiendo el formulario por defecto de Django.
    Añade los campos de email y grupos (roles).
    """
    email = forms.EmailField(required=True, label="Email")
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Roles/Grupos"
    )

    class Meta(UserCreationForm.Meta):
        model = User
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
    """
    Formulario para la edición de un usuario existente.
    """
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Roles/Grupos"
    )
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Permisos de Usuario"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')


class GroupForm(forms.ModelForm):
    """
    Formulario para la creación y edición de roles (grupos).
    """
    class Meta:
        model = Group
        fields = ['name']


# --- FORMULARIOS DE ALMACÉN ---

class ProveedorForm(forms.ModelForm):
    """
    Formulario para el modelo Proveedor.
    """
    class Meta:
        model = Proveedor
        fields = ['nombre', 'direccion', 'telefono', 'email', 'activo']


class CategoriaForm(forms.ModelForm):
    """
    Formulario para el modelo Categoria.
    """
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']


class ProductoForm(forms.ModelForm):
    """
    Formulario para el modelo Producto.
    """
    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'precio_venta', 'stock', 'descripcion', 'imagen', 'activo']


# --- FORMULARIOS DE COMPRA Y VENTA ---

class CompraForm(forms.ModelForm):
    """
    Formulario principal para el modelo Compra.
    """
    class Meta:
        model = Compra
        fields = ['proveedor']


DetalleCompraFormSet = inlineformset_factory(
    Compra,
    DetalleCompra,
    fields=('producto', 'cantidad', 'costo_unitario'),
    extra=1,
    can_delete=True
)

class VentaForm(forms.ModelForm):
    """
    Formulario principal para el modelo Venta.
    """
    class Meta:
        model = Venta
        # Corregido: El modelo Venta sí tiene un cliente.
        fields = ['cliente']


DetalleVentaFormSet = inlineformset_factory(
    Venta,
    DetalleVenta,
    fields=('producto', 'cantidad', 'precio_unitario'),
    extra=1,
    can_delete=True
)


# --- FORMULARIO DE CLIENTES ---

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['dni', 'nombrecompleto', 'telefono', 'email', 'activo']
        widgets = {
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'nombrecompleto': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class HabitacionForm(forms.ModelForm):
    class Meta:
        model = Habitacion
        fields = ['numero', 'piso', 'tipo', 'descripcion', 'activo']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
class TarifaForm(forms.ModelForm):
    class Meta:
        model = Tarifa
        fields = ['tipo_habitacion', 'nombre', 'tipo', 'duracion', 'precio']
        widgets = {
            'tipo_habitacion': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'duracion': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

# Utilidad para inputs bonitos
CONTROL = {"class": "form-control"}


# Cristal_app/forms.py

class ReservaOcuparForm(forms.ModelForm):
    # Simplificado: La vista ahora se encarga del valor inicial
    fecha_entrada = forms.DateTimeField(
        label="Fecha entrada",
        required=True,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"})
    )
    # ... (El resto de los campos de ReservaOcuparForm se quedan igual) ...
    fecha_salida = forms.SplitDateTimeField(
        label="Fecha / Hora salida",
        required=False, # Hacemos que no sea requerido, ya que se calcula con JS
        widget=forms.SplitDateTimeWidget(
            date_attrs={"type": "date", "class": "form-control"},
            time_attrs={"type": "time", "class": "form-control"},
        ),
    )
    total_calculado = forms.DecimalField(
        label="Total",
        max_digits=10, decimal_places=2, required=False, disabled=True,
        widget=forms.NumberInput(attrs={"class": "form-control", "readonly": True})
    )
    deuda_calculada = forms.DecimalField(
        label="A deuda",
        max_digits=10, decimal_places=2, required=False, disabled=True,
        widget=forms.NumberInput(attrs={"class": "form-control", "readonly": True})
    )

    class Meta:
        model = Reserva
        fields = [
            "cliente", "tarifa", "fecha_entrada", "fecha_salida",
            "descuento_monto", "observaciones",
        ]
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-control"}),
            "tarifa": forms.Select(attrs={"class": "form-control"}),
            "descuento_monto": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "value": "0"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ["tipo_pago", "monto_recibido"]
        widgets = {
            "tipo_pago": forms.Select(attrs={"class": "form-control"}),
            "monto_recibido": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"})
        }

class TipoPagoForm(forms.ModelForm):
    class Meta:
        model = TipoPago
        fields = ['nombre', 'descripcion', 'activo']

class AcompananteForm(forms.ModelForm):
    class Meta:
        model = Acompanante
        fields = ['nombre_completo', 'dni']
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DNI'}),
        }

# --- DEFINICIÓN ÚNICA Y CORRECTA DE AcompananteFormSet ---
AcompananteFormSet = inlineformset_factory(
    parent_model=Reserva,
    model=Acompanante,
    form=AcompananteForm,
    extra=1,
    can_delete=True
)