
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
# Importaciones de modelos
from .models import Compra, DetalleCompra, Venta, DetalleVenta, Producto, Cliente, Proveedor, Categoria
from django import forms
from django.forms import inlineformset_factory
from .models import Reserva, Pago, Acompanante

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
        # This is the line that needs to be corrected.
        # Assuming Venta is not directly linked to a Cliente, but to a Usuario.
        fields = [] # No fields needed, as 'usuario' is set in the view
        # If Venta should have a 'cliente' field, you must add it to the Venta model first.


DetalleVentaFormSet = inlineformset_factory(
    Venta,
    DetalleVenta,
    fields=('producto', 'cantidad', 'precio_unitario'),
    extra=1,
    can_delete=True
)


# --- FORMULARIO DE CLIENTES ---

class ClienteForm(forms.ModelForm):
    """
    Formulario para el modelo Cliente.
    """
    class Meta:
        model = Cliente
        fields = ['dni', 'nombrecompleto', 'telefono', 'email', 'activo']
_DATETIME_LOCAL_FMT = "%Y-%m-%dT%H:%M"

class ReservaForm(forms.ModelForm):
    # forzamos el widget datetime-local para poder MODIFICAR la salida
    fecha_salida = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
        input_formats=[_DATETIME_LOCAL_FMT],
        required=True,
        label="Fecha y hora de salida"
    )

    class Meta:
        model = Reserva
        # incluimos cliente y los campos que quieres editar al ocupar
        fields = ["cliente", "fecha_salida", "descuento_porcentaje", "observaciones"]
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-control"}),
            "descuento_porcentaje": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # solo clientes activos
        self.fields["cliente"].queryset = Cliente.objects.filter(activo=True)


class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ["tipo_pago", "monto_recibido"]
        widgets = {
            "tipo_pago": forms.Select(attrs={"class": "form-control"}),
            "monto_recibido": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
        }


class AcompananteForm(forms.ModelForm):
    class Meta:
        model = Acompanante
        fields = ["nombre_completo", "dni"]
        widgets = {
            "nombre_completo": forms.TextInput(attrs={"class": "form-control"}),
            "dni": forms.TextInput(attrs={"class": "form-control"}),
        }


AcompananteFormSet = inlineformset_factory(
    parent_model=Reserva,
    model=Acompanante,
    form=AcompananteForm,
    extra=1,
    can_delete=True
)