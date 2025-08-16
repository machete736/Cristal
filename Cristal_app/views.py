# Cristal_app/views.py

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.http import JsonResponse
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, View
from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.db.models import Sum, F, Prefetch
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.utils.dateformat import DateFormat
from django.shortcuts import render
from django.db.models import Sum
from dateutil.relativedelta import relativedelta
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from datetime import date, timedelta, datetime
# ...
hoy = datetime.now()
from .models import Reserva, Venta, Habitacion
# Modelos
from .models import (
    Piso, Habitacion, Reserva,
    Proveedor, Categoria, Producto,
    Compra, DetalleCompra, Venta, DetalleVenta,
    Cliente, TipoHabitacion, Tarifa, TipoPago, Consumo
)

# Formularios
from .forms import (
    CustomUserCreationForm, CustomUserChangeForm, GroupForm,
    CompraForm, DetalleCompraFormSet,
    VentaForm, DetalleVentaFormSet,
    ClienteForm, TarifaForm, ReservaOcuparForm, PagoForm, AcompananteFormSet, TipoPagoForm
)

User = get_user_model()


# =======================
# HOME / DASHBOARD
# =======================
@login_required
def home_view(request):
    total_habitaciones = Habitacion.objects.count()
    habitaciones_disponibles = Habitacion.objects.filter(estado='DISPONIBLE').count()
    habitaciones_ocupadas = Habitacion.objects.filter(estado='OCUPADA').count()
    habitaciones_limpieza = Habitacion.objects.filter(estado='LIMPIEZA').count()

    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    reservas_semanales = (
        Reserva.objects
        .filter(fecha_entrada__date__range=[start_of_week, end_of_week])
        .exclude(estado='CANCELADA')
        .count()
    )

    ingresos_semanales = (
        Reserva.objects
        .filter(fecha_entrada__date__range=[start_of_week, end_of_week])
        .exclude(estado='CANCELADA')
        .aggregate(total=Sum('costo_total'))['total'] or 0
    )

    context = {
        'total_habitaciones': total_habitaciones,
        'habitaciones_disponibles': habitaciones_disponibles,
        'habitaciones_ocupadas': habitaciones_ocupadas,
        'habitaciones_limpieza': habitaciones_limpieza,
        'reservas_semanales': reservas_semanales,
        'ingresos_semanales': ingresos_semanales,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
    }
    return render(request, 'Cristal_app/home.html', context)


# =======================
# RECEPCIÓN
# =======================
@login_required
def recepcion_view(request):
    """Tablero de Recepción por piso, con reserva activa en cada habitación."""
    pisos = Piso.objects.order_by('numero')

    # Piso seleccionado (o el primero)
    piso_id = request.GET.get('piso')
    piso_actual = get_object_or_404(Piso, pk=piso_id) if piso_id else pisos.first()

    # Prefetch de la reserva ACTIVA para cada habitación
    habitaciones = (
        Habitacion.objects
        .filter(piso=piso_actual)
        .select_related('piso', 'tipo')
        .prefetch_related(
            Prefetch(
                'reservas',
                queryset=Reserva.objects.filter(estado='ACTIVA').order_by('-fecha_entrada'),
                to_attr='reservas_activas'
            )
        )
        .order_by('numero')
    )

    # Agregar colores a las habitaciones según su estado
    for h in habitaciones:
        # Establecer el color según el estado de la habitación
        if h.estado == 'DISPONIBLE':
            h.color_estado = 'bg-green'  # Verde
        elif h.estado == 'OCUPADA':
            h.color_estado = 'bg-red'    # Rojo
        else:  # LIMPIEZA
            h.color_estado = 'bg-yellow'  # Amarillo

    # Productos para el modal de consumos
    productos = Producto.objects.filter(activo=True).order_by('nombre')

    context = {
        'pisos': pisos,
        'piso_actual': piso_actual,
        'habitaciones': habitaciones,
        'productos': productos,
    }

    return render(request, 'Cristal_app/Recepcion/recepcion.html', context)

def ocupar_habitacion(request, pk):
    hab = get_object_or_404(Habitacion, pk=pk)

    if hab.estado != "DISPONIBLE":
        messages.error(request, "La habitación no está disponible.")
        return redirect('recepcion')

    # El prefijo es crucial para que el formset funcione
    prefix_acompanantes = 'acompanantes'

    if request.method == 'POST':
        reserva = Reserva(habitacion=hab, estado='ACTIVA')
        rform = ReservaOcuparForm(request.POST, instance=reserva)
        pform = PagoForm(request.POST)
        aformset = AcompananteFormSet(request.POST, instance=reserva, prefix=prefix_acompanantes)

        if rform.is_valid() and pform.is_valid() and aformset.is_valid():
            with transaction.atomic():
                reserva_guardada = rform.save()

                pago = pform.save(commit=False)
                if pago.monto_recibido and pago.monto_recibido > 0:
                    pago.reserva = reserva_guardada
                    pago.save()

                aformset.instance = reserva_guardada
                aformset.save()

                hab.estado = 'OCUPADA'
                hab.save(update_fields=['estado'])

                messages.success(request, f'Habitación {hab.numero} ocupada correctamente.')
                piso_redirect = request.POST.get('piso')
                if piso_redirect:
                    return redirect(f"{reverse('recepcion')}?piso={piso_redirect}")
                return redirect('recepcion')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')

    else: # Método GET
        fe = timezone.now()
        initial = {
            # Formateamos la fecha para el input datetime-local
            'fecha_entrada': DateFormat(fe).format('Y-m-d\\TH:i'),
        }

        rform = ReservaOcuparForm(initial=initial)
        pform = PagoForm()
        aformset = AcompananteFormSet(instance=Reserva(), prefix=prefix_acompanantes)

    tarifas = hab.tipo.tarifas.all()
    clientes = Cliente.objects.filter(activo=True)
    cform_modal = ClienteForm()

    return render(request, 'Cristal_app/Recepcion/ocupar_form.html', {
        'habitacion': hab,
        'rform': rform,
        'pform': pform,
        'aformset': aformset,
        'clientes': clientes,
        'cform_modal': cform_modal,
        'tarifas': tarifas
    })
@login_required
def marcar_limpieza(request, pk):
    hab = get_object_or_404(Habitacion, pk=pk)
    if request.method == 'POST':
        hab.estado = 'LIMPIEZA'
        hab.save(update_fields=['estado'])
        messages.success(request, f'Habitación {hab.numero} marcada en limpieza.')
        next_piso = request.GET.get('piso') or request.POST.get('piso')
        return redirect(f"{reverse('recepcion')}?piso={next_piso}") if next_piso else redirect('recepcion')
    return render(request, 'Cristal_app/Recepcion/limpieza_confirm.html', {'habitacion': hab})

@login_required
def marcar_disponible(request, pk):
    hab = get_object_or_404(Habitacion, pk=pk)
    if request.method == 'POST':
        hab.estado = 'DISPONIBLE'
        hab.save(update_fields=['estado'])
        messages.success(request, f'Habitación {hab.numero} disponible nuevamente.')
        next_piso = request.GET.get('piso') or request.POST.get('piso')
        return redirect(f"{reverse('recepcion')}?piso={next_piso}") if next_piso else redirect('recepcion')
    return render(request, 'Cristal_app/Recepcion/disponible_confirm.html', {'habitacion': hab})

@login_required
def checkout_habitacion(request, pk):
    hab = get_object_or_404(Habitacion, pk=pk)
    reserva = Reserva.objects.filter(habitacion=hab, estado='ACTIVA').first()

    if not reserva:
        messages.error(request, 'No hay una reserva activa para esta habitación.')
        return redirect('recepcion')

    if request.method == 'POST':
        reserva.estado = 'FINALIZADA'
        reserva.fecha_salida = timezone.now()
        reserva.save(update_fields=['estado', 'fecha_salida'])
        hab.estado = 'DISPONIBLE'
        hab.save(update_fields=['estado'])

        messages.success(request, f'Checkout realizado. Habitación {hab.numero} disponible nuevamente.')
        return redirect('recepcion')  # Asegúrate de que esta ruta esté bien definida en tu `urls.py`

    return render(request, 'Cristal_app/Recepcion/checkout_confirm.html', {'habitacion': hab, 'reserva': reserva})

@login_required
def registrar_consumo(request, habitacion_id):
    # Obtener la habitación y la reserva activa
    hab = get_object_or_404(Habitacion, pk=habitacion_id)
    reserva = Reserva.objects.filter(habitacion=hab, estado='ACTIVA').first()  # Usamos first() para evitar múltiples resultados

    if not reserva:
        messages.error(request, 'No hay una reserva activa para esta habitación.')
        return redirect('recepcion')

    if request.method == 'POST':
        prod_ids = request.POST.getlist('producto_id[]')
        cantidades = request.POST.getlist('cantidad[]')
        next_url = request.POST.get('next') or reverse('recepcion')

        # Si no hay productos seleccionados, devuelve un error
        if not prod_ids:
            messages.error(request, 'Por favor, seleccione al menos un producto.')
            return redirect(next_url)

        with transaction.atomic():
            # Usar/crear venta asociada
            venta = reserva.venta or Venta.objects.create(cliente=reserva.cliente, usuario=request.user)
            if reserva.venta_id is None:
                reserva.venta = venta
                reserva.save(update_fields=['venta'])

            total_lineas = Decimal('0.00')
            for pid, cant in zip(prod_ids, cantidades):
                if not pid:
                    continue
                p = get_object_or_404(Producto, pk=pid)
                c = max(int(cant or 1), 1)

                # Crear el detalle de la venta
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=p,
                    cantidad=c,
                    precio_unitario=p.precio_venta
                )

                # Actualizar stock y calcular el total
                p.stock = F('stock') - c
                p.save(update_fields=['stock'])
                total_lineas += (p.precio_venta or 0) * c

            # Actualizar el total de la venta y de la reserva
            venta.total_venta = (venta.total_venta or 0) + total_lineas
            venta.save(update_fields=['total_venta'])

            reserva.costo_productos = (reserva.costo_productos or 0) + total_lineas
            if reserva.costo_total is not None:
                reserva.costo_total = (reserva.costo_total or 0) + total_lineas
            reserva.save(update_fields=['costo_productos', 'costo_total'])

        messages.success(request, 'Consumo registrado correctamente.')
        return redirect(next_url)
    return render(request, 'Cristal_app/Recepcion/consumo_form.html', {'habitacion': hab, 'reserva': reserva})

@login_required
def ver_detalles_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id)
    consumos = reserva.venta.detalleventa_set.all() if reserva.venta else []
    context = {
        'reserva': reserva,
        'consumos': consumos,
    }
    return render(request, 'Cristal_app/Recepcion/detalles_reserva.html', context)

@property
def reserva_activa(self):
    return self.reservas.filter(estado='ACTIVA').order_by('-fecha_entrada').first()

# =======================
# CRUD USUARIOS
# =======================
class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    template_name = 'Cristal_app/Acceso/usuarios/user_list.html'
    context_object_name = 'users'
    permission_required = 'auth.view_user'


class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'Cristal_app/Acceso/usuarios/user_form.html'
    success_url = reverse_lazy('user_list')
    success_message = "Usuario '%(username)s' creado exitosamente."
    permission_required = 'auth.add_user'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Crear'
        return ctx


class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'Cristal_app/Acceso/usuarios/user_form.html'
    context_object_name = 'user'
    success_url = reverse_lazy('user_list')
    success_message = "Usuario '%(username)s' actualizado exitosamente."
    permission_required = 'auth.change_user'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Editar'
        return ctx


class UserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = User
    template_name = 'Cristal_app/Acceso/usuarios/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')
    context_object_name = 'user'
    permission_required = 'auth.delete_user'

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        username = obj.username
        obj.delete()
        messages.success(request, f"Usuario '{username}' eliminado exitosamente.")
        return redirect(self.success_url)


# =======================
# CRUD ROLES
# =======================
class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Group
    template_name = 'Cristal_app/Acceso/roles/group_list.html'
    context_object_name = 'groups'
    permission_required = 'auth.view_group'


class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'Cristal_app/Acceso/roles/group_form.html'
    success_url = reverse_lazy('group_list')
    success_message = "Rol '%(name)s' creado exitosamente."
    permission_required = 'auth.add_group'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Crear'
        return ctx


class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'Cristal_app/Acceso/roles/group_form.html'
    context_object_name = 'group'
    success_url = reverse_lazy('group_list')
    success_message = "Rol '%(name)s' actualizado exitosamente."
    permission_required = 'auth.change_group'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Editar'
        return ctx


class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Group
    template_name = 'Cristal_app/Acceso/roles/group_confirm_delete.html'
    success_url = reverse_lazy('group_list')
    context_object_name = 'group'
    success_message = "Rol '%(name)s' eliminado exitosamente."
    permission_required = 'auth.delete_group'

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        name = obj.name
        obj.delete()
        messages.success(request, f"Rol '{name}' eliminado exitosamente.")
        return redirect(self.success_url)


# =======================
# CRUD ALMACÉN
# =======================
class ProveedorListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Proveedor
    template_name = 'Cristal_app/Almacen/Proveedores/proveedor_list.html'
    context_object_name = 'proveedores'
    permission_required = 'Cristal_app.view_proveedor'


class ProveedorCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Proveedor
    fields = ['nombre', 'direccion', 'telefono', 'email']
    template_name = 'Cristal_app/Almacen/Proveedores/proveedor_form.html'
    success_url = reverse_lazy('proveedor_list')
    success_message = "Proveedor '%(nombre)s' creado exitosamente."
    permission_required = 'Cristal_app.add_proveedor'


class ProveedorUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Proveedor
    fields = ['nombre', 'direccion', 'telefono', 'email', 'activo']
    template_name = 'Cristal_app/Almacen/Proveedores/proveedor_form.html'
    context_object_name = 'proveedor'
    success_url = reverse_lazy('proveedor_list')
    success_message = "Proveedor '%(nombre)s' actualizado exitosamente."
    permission_required = 'Cristal_app.change_proveedor'


class ProveedorDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Proveedor
    template_name = 'Cristal_app/Almacen/Proveedores/proveedor_confirm_delete.html'
    success_url = reverse_lazy('proveedor_list')
    context_object_name = 'proveedor'
    success_message = "Proveedor eliminado exitosamente."
    permission_required = 'Cristal_app.delete_proveedor'


class CategoriaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Categoria
    template_name = 'Cristal_app/Almacen/Categorias/categoria_list.html'
    context_object_name = 'categorias'
    permission_required = 'Cristal_app.view_categoria'


class CategoriaCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Categoria
    fields = ['nombre', 'descripcion']
    template_name = 'Cristal_app/Almacen/Categorias/categoria_form.html'
    success_url = reverse_lazy('categoria_list')
    success_message = "Categoría '%(nombre)s' creada exitosamente."
    permission_required = 'Cristal_app.add_categoria'


class CategoriaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Categoria
    fields = ['nombre', 'descripcion']
    template_name = 'Cristal_app/Almacen/Categorias/categoria_form.html'
    context_object_name = 'categoria'
    success_url = reverse_lazy('categoria_list')
    success_message = "Categoría '%(nombre)s' actualizada exitosamente."
    permission_required = 'Cristal_app.change_categoria'


class CategoriaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Categoria
    template_name = 'Cristal_app/Almacen/Categorias/categoria_confirm_delete.html'
    success_url = reverse_lazy('categoria_list')
    context_object_name = 'categoria'
    success_message = "Categoría eliminada exitosamente."
    permission_required = 'Cristal_app.delete_categoria'


class ProductoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Producto
    template_name = 'Cristal_app/Almacen/Productos/producto_list.html'
    context_object_name = 'productos'
    permission_required = 'Cristal_app.view_producto'


class ProductoCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Producto
    fields = ['nombre', 'categoria', 'precio_venta', 'stock', 'descripcion', 'imagen']
    template_name = 'Cristal_app/Almacen/Productos/producto_form.html'
    success_url = reverse_lazy('producto_list')
    success_message = "Producto '%(nombre)s' creado exitosamente."
    permission_required = 'Cristal_app.add_producto'


class ProductoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Producto
    fields = ['nombre', 'categoria', 'precio_venta', 'stock', 'descripcion', 'imagen', 'activo']
    template_name = 'Cristal_app/Almacen/Productos/producto_form.html'
    context_object_name = 'producto'
    success_url = reverse_lazy('producto_list')
    success_message = "Producto '%(nombre)s' actualizado exitosamente."
    permission_required = 'Cristal_app.change_producto'


class ProductoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Producto
    template_name = 'Cristal_app/Almacen/Productos/producto_confirm_delete.html'
    success_url = reverse_lazy('producto_list')
    context_object_name = 'producto'
    success_message = "Producto eliminado exitosamente."
    permission_required = 'Cristal_app.delete_producto'


# =======================
# COMPRAS
# =======================
class CompraListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Compra
    template_name = 'Cristal_app/Almacen/Compra/compra_list.html'
    context_object_name = 'compras'
    permission_required = 'Cristal_app.view_compra'


class CompraCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'Cristal_app.add_compra'
    template_name = 'Cristal_app/Almacen/Compra/compra_form.html'

    def get(self, request, *args, **kwargs):
        form = CompraForm()
        fs = DetalleCompraFormSet(queryset=DetalleCompra.objects.none())
        return render(request, self.template_name, {'form': form, 'formset': fs})

    def post(self, request, *args, **kwargs):
        form = CompraForm(request.POST)
        fs = DetalleCompraFormSet(request.POST)
        if form.is_valid() and fs.is_valid():
            with transaction.atomic():
                c = form.save(commit=False)
                c.usuario = request.user
                c.save()
                total = Decimal('0')
                for df in fs:
                    if df.cleaned_data and not df.cleaned_data.get('DELETE'):
                        d = df.save(commit=False)
                        d.compra = c
                        d.save()
                        d.producto.stock += d.cantidad
                        d.producto.save()
                        total += Decimal(d.cantidad) * Decimal(d.costo_unitario)
                c.total_compra = total
                c.save()
            messages.success(request, f"Compra #{c.pk} creada.")
            return redirect('compra_list')
        messages.error(request, "Error en el formulario.")
        return render(request, self.template_name, {'form': form, 'formset': fs})


class CompraUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'Cristal_app.change_compra'
    template_name = 'Cristal_app/Almacen/Compra/compra_form.html'

    def get(self, request, pk, *args, **kwargs):
        c = get_object_or_404(Compra, pk=pk)
        return render(request, self.template_name, {
            'form': CompraForm(instance=c),
            'formset': DetalleCompraFormSet(instance=c),
            'compra': c
        })

    def post(self, request, pk, *args, **kwargs):
        c = get_object_or_404(Compra, pk=pk)
        form = CompraForm(request.POST, instance=c)
        fs = DetalleCompraFormSet(request.POST, instance=c)
        if form.is_valid() and fs.is_valid():
            with transaction.atomic():
                # revertir stock anterior
                for d in DetalleCompra.objects.filter(compra=c):
                    d.producto.stock -= d.cantidad
                    d.producto.save()
                form.save()
                fs.save()
                total = Decimal('0')
                for d in DetalleCompra.objects.filter(compra=c):
                    d.producto.stock += d.cantidad
                    d.producto.save()
                    total += Decimal(d.cantidad) * Decimal(d.costo_unitario)
                c.total_compra = total
                c.save()
            messages.success(request, f"Compra #{c.pk} actualizada.")
            return redirect('compra_list')
        messages.error(request, "Error en el formulario.")
        return render(request, self.template_name, {'form': form, 'formset': fs, 'compra': c})


class CompraDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Compra
    template_name = 'Cristal_app/Almacen/Compra/compra_confirm_delete.html'
    success_url = reverse_lazy('compra_list')
    context_object_name = 'compra'
    permission_required = 'Cristal_app.delete_compra'

    def delete(self, request, *args, **kwargs):
        c = self.get_object()
        for d in DetalleCompra.objects.filter(compra=c):
            d.producto.stock -= d.cantidad
            d.producto.save()
        c.delete()
        messages.success(request, "Compra eliminada.")
        return redirect(self.success_url)


# =======================
# VENTAS
# =======================
class VentaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Venta
    template_name = 'Cristal_app/Almacen/Venta/venta_list.html'
    context_object_name = 'ventas'
    permission_required = 'Cristal_app.view_venta'


class VentaCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'Cristal_app.add_venta'
    template_name = 'Cristal_app/Almacen/Venta/venta_form.html'

    def get(self, request, *args, **kwargs):
        form = VentaForm()
        fs = DetalleVentaFormSet(queryset=DetalleVenta.objects.none())
        return render(request, self.template_name, {'form': form, 'formset': fs})

    def post(self, request, *args, **kwargs):
        form = VentaForm(request.POST)
        fs = DetalleVentaFormSet(request.POST)
        if form.is_valid() and fs.is_valid():
            with transaction.atomic():
                v = form.save(commit=False)
                v.usuario = request.user
                v.save()
                total = Decimal('0')
                for df in fs:
                    if df.cleaned_data and not df.cleaned_data.get('DELETE'):
                        d = df.save(commit=False)
                        d.venta = v
                        d.save()
                        d.producto.stock -= d.cantidad
                        d.producto.save()
                        total += Decimal(d.cantidad) * Decimal(d.precio_unitario)
                v.total_venta = total
                v.save()
            messages.success(request, f"Venta #{v.pk} creada.")
            return redirect('venta_list')
        messages.error(request, "Error en el formulario.")
        return render(request, self.template_name, {'form': form, 'formset': fs})


class VentaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'Cristal_app.change_venta'
    template_name = 'Cristal_app/Almacen/Venta/venta_form.html'

    def get(self, request, pk, *args, **kwargs):
        v = get_object_or_404(Venta, pk=pk)
        return render(request, self.template_name, {
            'form': VentaForm(instance=v),
            'formset': DetalleVentaFormSet(instance=v),
            'venta': v
        })

    def post(self, request, pk, *args, **kwargs):
        v = get_object_or_404(Venta, pk=pk)
        form = VentaForm(request.POST, instance=v)
        fs = DetalleVentaFormSet(request.POST, instance=v)
        if form.is_valid() and fs.is_valid():
            with transaction.atomic():
                for d in DetalleVenta.objects.filter(venta=v):
                    d.producto.stock += d.cantidad
                    d.producto.save()
                form.save()
                fs.save()
                total = Decimal('0')
                for d in DetalleVenta.objects.filter(venta=v):
                    d.producto.stock -= d.cantidad
                    d.producto.save()
                    total += Decimal(d.cantidad) * Decimal(d.precio_unitario)
                v.total_venta = total
                v.save()
            messages.success(request, f"Venta #{v.pk} actualizada.")
            return redirect('venta_list')
        messages.error(request, "Error en el formulario.")
        return render(request, self.template_name, {'form': form, 'formset': fs, 'venta': v})


class VentaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Venta
    template_name = 'Cristal_app/Almacen/Venta/venta_confirm_delete.html'
    success_url = reverse_lazy('venta_list')
    context_object_name = 'venta'
    permission_required = 'Cristal_app.delete_venta'

    def delete(self, request, *args, **kwargs):
        v = self.get_object()
        for d in DetalleVenta.objects.filter(venta=v):
            d.producto.stock += d.cantidad
            d.producto.save()
        v.delete()
        messages.success(request, "Venta eliminada.")
        return redirect(self.success_url)


# =======================
# CLIENTES
# =======================
class ClienteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Cliente
    template_name = 'Cristal_app/Cliente/cliente_list.html'
    context_object_name = 'clientes'
    permission_required = 'Cristal_app.view_cliente'


class ClienteCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'Cristal_app/Cliente/cliente_form.html'
    success_url = reverse_lazy('cliente_list')
    success_message = "Cliente '%(nombrecompleto)s' creado exitosamente."
    permission_required = 'Cristal_app.add_cliente'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Crear'
        return ctx


class ClienteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'Cristal_app/Cliente/cliente_form.html'
    context_object_name = 'cliente'
    success_url = reverse_lazy('cliente_list')
    success_message = "Cliente '%(nombrecompleto)s' actualizado exitosamente."
    permission_required = 'Cristal_app.change_cliente'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Editar'
        return ctx


class ClienteDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'Cristal_app/Cliente/cliente_confirm_delete.html'
    success_url = reverse_lazy('cliente_list')
    context_object_name = 'cliente'
    permission_required = 'Cristal_app.delete_cliente'

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        name = obj.nombrecompleto
        obj.delete()
        messages.success(request, f"Cliente '{name}' eliminado exitosamente.")
        return redirect(self.success_url)


# =======================
# MANTENIMIENTO
# =======================

def gestionar_tarifas(request, pk):
    tipo_habitacion = get_object_or_404(TipoHabitacion, pk=pk)
    tarifas = tipo_habitacion.tarifas.all()  # Obtiene todas las tarifas del tipo de habitación
    context = {'tipo_habitacion': tipo_habitacion, 'tarifas': tarifas}
    return render(request, 'Cristal_app/Tarifa/gestionar_tarifas.html', context)

def editar_tarifa(request, pk=None, tipo_id=None):
    # Si pk es None, significa que estamos creando una nueva tarifa
    if pk is None:
        tipo_habitacion = get_object_or_404(TipoHabitacion, pk=tipo_id)
        tarifa = Tarifa(tipo_habitacion=tipo_habitacion)  # Nueva tarifa asociada al tipo
    else:
        tarifa = get_object_or_404(Tarifa, pk=pk)

    if request.method == 'POST':
        form = TarifaForm(request.POST, instance=tarifa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tarifa guardada con éxito.')
            return redirect('gestionar_tarifas', pk=tarifa.tipo_habitacion.pk)
    else:
        form = TarifaForm(instance=tarifa)

    return render(request, 'Cristal_app/Tarifa/editar_tarifa.html', {'form': form})

def eliminar_tarifa(request, pk):
    tarifa = get_object_or_404(Tarifa, pk=pk)
    tipo_habitacion = tarifa.tipo_habitacion
    tarifa.delete()
    messages.success(request, 'Tarifa eliminada con éxito.')
    return redirect('gestionar_tarifas', pk=tipo_habitacion.pk)
def obtener_tarifas(request, tipo_id):
    tipo_habitacion = get_object_or_404(TipoHabitacion, pk=tipo_id)
    tarifas = tipo_habitacion.tarifas.all().values('nombre', 'precio', 'tipo')
    return JsonResponse({'tarifas': list(tarifas)})

class TipoHabitacionCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = TipoHabitacion
    fields = ['nombre', 'descripcion', 'activo']
    template_name = 'Cristal_app/Mantenimiento/TipoHabitacion/tipohabitacion_form.html'
    success_url = reverse_lazy('tipohabitacion_list')  # Redirige a la lista después de crear
    success_message = "Tipo de habitación '%(nombre)s' creado exitosamente."
    permission_required = 'Cristal_app.add_tipohabitacion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
class TipoHabitacionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TipoHabitacion
    template_name = 'Cristal_app/Mantenimiento/TipoHabitacion/tipohabitacion_list.html'
    context_object_name = 'tipohabitaciones'
    permission_required = 'Cristal_app.view_tipohabitacion'



class TipoHabitacionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = TipoHabitacion
    fields = ['nombre', 'descripcion', 'activo']
    template_name = 'Cristal_app/Mantenimiento/TipoHabitacion/tipohabitacion_form.html'
    success_url = reverse_lazy('tipohabitacion_list')
    success_message = "Tipo de Habitación '%(nombre)s' actualizado exitosamente."
    permission_required = 'Cristal_app.change_tipohabitacion'


class TipoHabitacionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = TipoHabitacion
    template_name = 'Cristal_app/Mantenimiento/TipoHabitacion/tipohabitacion_confirm_delete.html'
    success_url = reverse_lazy('tipohabitacion_list')
    context_object_name = 'object'
    permission_required = 'Cristal_app.delete_tipohabitacion'

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        name = obj.nombre
        obj.delete()
        messages.success(request, f"Tipo de Habitación '{name}' eliminado exitosamente.")
        return redirect(self.success_url)


class PisoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Piso
    template_name = 'Cristal_app/Mantenimiento/Pisos/piso_list.html'
    context_object_name = 'pisos'
    permission_required = 'Cristal_app.view_piso'


class PisoCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Piso
    fields = ['numero', 'descripcion', 'activo']
    template_name = 'Cristal_app/Mantenimiento/Pisos/piso_form.html'
    success_url = reverse_lazy('piso_list')
    success_message = "Piso '%(numero)s' creado exitosamente."
    permission_required = 'Cristal_app.add_piso'


class PisoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Piso
    fields = ['numero', 'descripcion', 'activo']
    template_name = 'Cristal_app/Mantenimiento/Pisos/piso_form.html'
    success_url = reverse_lazy('piso_list')
    success_message = "Piso '%(numero)s' actualizado exitosamente."
    permission_required = 'Cristal_app.change_piso'


class PisoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Piso
    template_name = 'Cristal_app/Mantenimiento/Pisos/piso_confirm_delete.html'
    success_url = reverse_lazy('piso_list')
    context_object_name = 'object'
    permission_required = 'Cristal_app.delete_piso'

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        num = obj.numero
        obj.delete()
        messages.success(request, f"Piso '{num}' eliminado exitosamente.")
        return redirect(self.success_url)


class HabitacionCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Habitacion
    fields = ['numero', 'piso', 'tipo', 'descripcion', 'activo']
    template_name = 'Cristal_app/Mantenimiento/Habitacion/habitacion_form.html'
    success_url = reverse_lazy('habitacion_list')
    success_message = "Habitación '%(numero)s' creada exitosamente."
    permission_required = 'Cristal_app.add_habitacion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener el tipo de habitación del formulario
        tipo_id = self.request.GET.get('tipo')

        if tipo_id:
            tipo_habitacion = get_object_or_404(TipoHabitacion, pk=tipo_id)
            context['tarifas'] = tipo_habitacion.tarifas.all()  # Pasa las tarifas a la plantilla
        else:
            context['tarifas'] = []  # Si no hay tipo, no pasa ninguna tarifa

        return context


class HabitacionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Habitacion
    template_name = 'Cristal_app/Mantenimiento/Habitacion/habitacion_list.html'
    context_object_name = 'habitaciones'
    permission_required = 'Cristal_app.view_habitacion'

    def get_queryset(self):
        queryset = super().get_queryset()
        # Prevenir múltiples consultas a la base de datos utilizando select_related para obtener el tipo de habitación
        return queryset.select_related('tipo')  # Esto traerá la relación TipoHabitacion asociada a cada habitación

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar las tarifas al contexto
        for habitacion in context['habitaciones']:
            habitacion.tarifas = habitacion.tipo.tarifas.all()  # Aquí obtenemos las tarifas asociadas al tipo de habitación
        return context


class HabitacionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Habitacion
    fields = ['numero', 'piso', 'tipo', 'descripcion', 'precio_noche', 'activo']
    template_name = 'Cristal_app/Mantenimiento/Habitacion/habitacion_form.html'
    success_url = reverse_lazy('habitacion_list')
    success_message = "Habitación '%(numero)s' actualizada exitosamente."

    # Aquí defines los permisos necesarios para acceder a esta vista
    permission_required = 'Cristal_app.change_habitacion'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipos_habitacion'] = TipoHabitacion.objects.all()  # Pasa los tipos de habitación al formulario
        return context


class HabitacionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Habitacion
    template_name = 'Cristal_app/Mantenimiento/Habitacion/habitacion_confirm_delete.html'
    success_url = reverse_lazy('habitacion_list')
    context_object_name = 'object'
    permission_required = 'Cristal_app.delete_habitacion'

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        num = obj.numero
        obj.delete()
        messages.success(request, f"Habitación '{num}' eliminada exitosamente.")
        return redirect(self.success_url)


# Listar Tipos de Pago
def tipo_pago_list(request):
    tipos_pago = TipoPago.objects.all()
    return render(request, 'Cristal_app/TipoPago/tipopago_list.html', {'tipos_pago': tipos_pago})


# Crear o Editar Tipo de Pago
def tipo_pago_create_or_update(request, pk=None):
    if pk:
        tipo_pago = get_object_or_404(TipoPago, pk=pk)
    else:
        tipo_pago = None

    if request.method == 'POST':
        form = TipoPagoForm(request.POST, instance=tipo_pago)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de pago guardado correctamente.')
            return redirect('tipopago_list')
        else:
            messages.error(request, 'Error al guardar el tipo de pago.')
    else:
        form = TipoPagoForm(instance=tipo_pago)

    return render(request, 'Cristal_app/TipoPago/tipopago_form.html', {'form': form})


# Eliminar Tipo de Pago
def tipo_pago_delete(request, pk):
    tipo_pago = get_object_or_404(TipoPago, pk=pk)
    tipo_pago.delete()
    messages.success(request, 'Tipo de pago eliminado correctamente.')
    return redirect('tipopago_list')


def tipo_pago_create_or_update(request, pk=None):
    if pk:
        tipo_pago = get_object_or_404(TipoPago, pk=pk)
    else:
        tipo_pago = None

    if request.method == 'POST':
        form = TipoPagoForm(request.POST, instance=tipo_pago)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de pago guardado correctamente.')
            return redirect('tipopago_list')
        else:
            messages.error(request, 'Error al guardar el tipo de pago.')
    else:
        form = TipoPagoForm(instance=tipo_pago)

    return render(request, 'Cristal_app/TipoPago/tipopago_form.html', {'form': form})
# Cristal_app/views.py

from django.http import JsonResponse # Asegúrate de que esté importado
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

# ... (el resto de tus vistas)

@login_required
@require_POST # Esta vista solo aceptará peticiones POST
def crear_cliente_ajax(request):
    """Crea un cliente vía AJAX y devuelve sus datos en JSON."""
    form = ClienteForm(request.POST)
    if form.is_valid():
        cliente = form.save()
        return JsonResponse({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'nombrecompleto': cliente.nombrecompleto
            }
        })
    # Si el formulario no es válido, devuelve los errores
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


# Reporte de Reservas por Fecha
def reporte_reservas(request):
    periodo = request.GET.get('periodo', 'hoy')  # 'hoy', 'semana', 'mes', 'personalizado'
    fecha_inicio = None
    fecha_fin = None

    hoy = date.today()

    if periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=hoy.weekday())
        fecha_fin = fecha_inicio + timedelta(days=6)
    elif periodo == 'mes':
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy.replace(day=1) + timedelta(days=32)
        fecha_fin = fecha_fin.replace(day=1) - timedelta(days=1)
    else:  # 'hoy' o por defecto
        fecha_inicio = hoy
        fecha_fin = hoy

    reservas = Reserva.objects.filter(fecha_entrada__date__range=[fecha_inicio, fecha_fin])

    context = {
        'reservas': reservas,
        'periodo_seleccionado': periodo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }

    # Renderizar HTML para la página
    return render(request, 'Cristal_app/reportes/reporte_reservas.html', context)


def generar_pdf(request):
    # Lógica de filtrado de datos (duplicada de reporte_reservas)
    periodo = request.GET.get('periodo', 'hoy')
    fecha_inicio = None
    fecha_fin = None

    hoy = date.today()

    if periodo == 'semana':
        # Resta los días de la semana para llegar al lunes (0=lunes, 1=martes...)
        fecha_inicio = hoy - timedelta(days=hoy.weekday())
        fecha_fin = fecha_inicio + timedelta(days=6)
    elif periodo == 'mes':
        fecha_inicio = hoy.replace(day=1)
        # Suma 32 días y luego vuelve al primer día del siguiente mes, restándole un día
        fecha_fin = (hoy.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:  # 'hoy' o por defecto
        fecha_inicio = hoy
        fecha_fin = hoy

    reservas = Reserva.objects.filter(fecha_entrada__date__range=[fecha_inicio, fecha_fin])

    template_path = 'Cristal_app/reportes/reporte_reservas_pdf.html'
    context = {'reservas': reservas, 'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin}
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_reservas.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error al generar el PDF <pre>' + html + '</pre>')

    return response


# Reporte de Consumos Totales
# Reporte de Consumos Totales
def reporte_consumos(request):
    consumos_totales = Venta.objects.aggregate(total_consumo=Sum('total_venta'))

    context = {
        'total_consumo': consumos_totales['total_consumo'],
    }
    return render(request, 'Cristal_app/reportes/reporte_consumos.html', context)

# Reporte de Habitaciones Ocupadas
# Reporte de Habitaciones Ocupadas
def reporte_habitaciones_ocupadas(request):
    habitaciones_ocupadas = Habitacion.objects.filter(estado='OCUPADA')

    context = {
        'habitaciones_ocupadas': habitaciones_ocupadas,
    }
    return render(request, 'Cristal_app/reportes/reporte_habitaciones_ocupadas.html', context)
def reporte_ingresos(request):
    # Calcula el total de ingresos de las ventas
    ventas_ingresos = Venta.objects.aggregate(total_ingresos=Sum('total_venta'))['total_ingresos'] or 0

    # Calcula el total de ingresos de las reservas
    # Asume que tienes un campo 'precio_total' o similar en tu modelo Reserva
    # y que solo consideras las reservas con estado 'CONFIRMADA'
    reservas_ingresos = Reserva.objects.filter(estado='CONFIRMADA').aggregate(total_ingresos=Sum('precio_total'))['total_ingresos'] or 0

    total_ingresos = ventas_ingresos + reservas_ingresos

    context = {
        'total_ingresos': total_ingresos,
    }
    return render(request, 'Cristal_app/reportes/reporte_ingresos.html', context)


@login_required
def reporte_ingresos(request):
    periodo = request.GET.get('periodo', 'hoy')
    fecha_inicio = None
    fecha_fin = None

    hoy = date.today()

    if periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=hoy.weekday())
        fecha_fin = fecha_inicio + timedelta(days=6)
    elif periodo == 'mes':
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = (hoy.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:
        fecha_inicio = hoy
        fecha_fin = hoy

    # Calcular ingresos de ventas
    ventas_ingresos = Venta.objects.filter(fecha_venta__date__range=[fecha_inicio, fecha_fin]).aggregate(
        total_ingresos=Sum('total_venta'))['total_ingresos'] or 0

    # Calcular ingresos de reservas - ¡CORRECCIÓN AQUÍ!
    # Se reemplaza 'precio_total' por 'costo_total'
    reservas_ingresos = \
    Reserva.objects.filter(fecha_entrada__date__range=[fecha_inicio, fecha_fin], estado='CONFIRMADA').aggregate(
        total_ingresos=Sum('costo_total'))['total_ingresos'] or 0

    total_ingresos = ventas_ingresos + reservas_ingresos

    context = {
        'ventas_ingresos': ventas_ingresos,
        'reservas_ingresos': reservas_ingresos,
        'total_ingresos': total_ingresos,
        'usuario': request.user,
        'fecha_generacion': hoy,
        'periodo_seleccionado': periodo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }

    return render(request, 'Cristal_app/reportes/reporte_ingresos.html', context)


def generar_pdf_ingresos(request):
    periodo = request.GET.get('periodo', 'hoy')
    fecha_inicio = None
    fecha_fin = None
    hoy = date.today()

    if periodo == 'semana':
        fecha_inicio = hoy - timedelta(days=hoy.weekday())
        fecha_fin = fecha_inicio + timedelta(days=6)
    elif periodo == 'mes':
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = (hoy.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:
        fecha_inicio = hoy
        fecha_fin = hoy

    ventas_ingresos = Venta.objects.filter(fecha_venta__date__range=[fecha_inicio, fecha_fin]).aggregate(
        total_ingresos=Sum('total_venta'))['total_ingresos'] or 0
    reservas_ingresos = \
    Reserva.objects.filter(fecha_entrada__date__range=[fecha_inicio, fecha_fin], estado='CONFIRMADA').aggregate(
        total_ingresos=Sum('precio_total'))['total_ingresos'] or 0

    total_ingresos = ventas_ingresos + reservas_ingresos

    template_path = 'Cristal_app/reportes/reporte_ingresos_pdf.html'
    context = {
        'ventas_ingresos': ventas_ingresos,
        'reservas_ingresos': reservas_ingresos,
        'total_ingresos': total_ingresos,
        'usuario': request.user,
        'fecha_generacion': hoy,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }

    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_ingresos.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF <pre>' + html + '</pre>')
    return response


@login_required
def reporte_resumen(request):
    periodo = request.GET.get('periodo', 'semana')  # Por defecto, 'semana'
    fecha_inicio = None
    fecha_fin = None

    hoy = date.today()

    if periodo == 'dia':
        fecha_inicio = hoy
        fecha_fin = hoy
    elif periodo == 'mes':
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
    elif periodo == 'anual':
        fecha_inicio = hoy.replace(month=1, day=1)
        fecha_fin = hoy.replace(month=12, day=31)
    else:  # 'semana' o cualquier otro valor
        fecha_inicio = hoy - timedelta(days=hoy.weekday())
        fecha_fin = fecha_inicio + timedelta(days=6)

    # Cálculo de ingresos y consumos para el periodo seleccionado
    ventas = Venta.objects.filter(fecha_venta__date__range=[fecha_inicio, fecha_fin]).aggregate(
        total_ingresos=Sum('total_venta'))['total_ingresos'] or 0
    reservas = \
    Reserva.objects.filter(fecha_entrada__date__range=[fecha_inicio, fecha_fin], estado='CONFIRMADA').aggregate(
        total_ingresos=Sum('costo_total'))['total_ingresos'] or 0
    total_ingresos = ventas + reservas

    consumos = \
    Consumo.objects.filter(fecha__date__range=[fecha_inicio, fecha_fin]).aggregate(total_consumos=Sum('monto_consumo'))[
        'total_consumos'] or 0

    context = {
        'ventas': ventas,
        'reservas': reservas,
        'total_ingresos': total_ingresos,
        'consumos': consumos,
        'usuario': request.user,
        'fecha_generacion': hoy,
        'periodo_seleccionado': periodo,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }

    return render(request, 'Cristal_app/reportes/reporte_resumen.html', context)


# Vista para generar el PDF
def generar_pdf_resumen(request):
    periodo = request.GET.get('periodo', 'semana')
    fecha_inicio = None
    fecha_fin = None
    hoy = date.today()

    # Mismo código de filtrado que en reporte_resumen
    if periodo == 'dia':
        fecha_inicio = hoy
        fecha_fin = hoy
    elif periodo == 'mes':
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
    elif periodo == 'anual':
        fecha_inicio = hoy.replace(month=1, day=1)
        fecha_fin = hoy.replace(month=12, day=31)
    else:  # 'semana' o cualquier otro valor
        fecha_inicio = hoy - timedelta(days=hoy.weekday())
        fecha_fin = fecha_inicio + timedelta(days=6)

    ventas = Venta.objects.filter(fecha_venta__date__range=[fecha_inicio, fecha_fin]).aggregate(
        total_ingresos=Sum('total_venta'))['total_ingresos'] or 0
    reservas = \
    Reserva.objects.filter(fecha_entrada__date__range=[fecha_inicio, fecha_fin], estado='CONFIRMADA').aggregate(
        total_ingresos=Sum('costo_total'))['total_ingresos'] or 0
    total_ingresos = ventas + reservas
    consumos = \
    Consumo.objects.filter(fecha__date__range=[fecha_inicio, fecha_fin]).aggregate(total_consumos=Sum('monto_consumo'))[
        'total_consumos'] or 0

    template_path = 'Cristal_app/reportes/reporte_resumen_pdf.html'
    context = {
        'ventas': ventas,
        'reservas': reservas,
        'total_ingresos': total_ingresos,
        'consumos': consumos,
        'usuario': request.user,
        'fecha_generacion': hoy,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'periodo_seleccionado': periodo,
    }

    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_resumen.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF <pre>' + html + '</pre>')
    return response
