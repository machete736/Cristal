# Cristal_app/views.py
from decimal import Decimal
from datetime import timedelta
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, View
from django.views.decorators.http import require_POST
from collections import defaultdict
from django.db.models import Prefetch
# Modelos
from .models import (
    Piso, Habitacion, Reserva,
    Proveedor, Categoria, Producto,
    Compra, DetalleCompra, Venta, DetalleVenta,
    Cliente, TipoHabitacion
)

# Formularios
from .forms import (
    CustomUserCreationForm, CustomUserChangeForm, GroupForm,
    CompraForm, DetalleCompraFormSet,
    VentaForm, DetalleVentaFormSet,
    ClienteForm, ReservaForm, PagoForm, AcompananteFormSet
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
def recepcion_view(request):
    pisos = Piso.objects.filter(activo=True).order_by('numero')

    # Piso seleccionado en la URL (?piso=ID); si no, el primero activo
    piso_id = request.GET.get('piso')
    if piso_id:
        piso_actual = get_object_or_404(Piso, pk=piso_id)
    else:
        piso_actual = pisos.first() if pisos.exists() else None

    # Habitaciones del piso actual
    if piso_actual:
        habitaciones = (Habitacion.objects
                        .filter(activo=True, piso=piso_actual)
                        .select_related('tipo', 'piso')
                        .order_by('numero'))
    else:
        habitaciones = Habitacion.objects.none()

    # >>>>>>>>>> AQUÍ VA EL BLOQUE CLAVE <<<<<<<<<<
    # Enlaza a cada habitación su reserva activa para evitar N+1 queries
    if habitaciones.exists():
        activas = (
            Reserva.objects
            .filter(estado='ACTIVA', habitacion__in=habitaciones)
            .select_related('cliente', 'venta')  # objetos relacionados 1-1 / FK
            .prefetch_related('acompanantes', 'venta__detalleventa_set__producto')  # m2m/one-to-many
        )
        mapa = {r.habitacion_id: r for r in activas}
        for h in habitaciones:
            h.reserva_activa = mapa.get(h.id)
    else:
        # Si no hay habitaciones, evita errores en plantilla
        for h in habitaciones:
            h.reserva_activa = None
    # >>>>>>>>> FIN BLOQUE CLAVE <<<<<<<<<

    # Productos disponibles (para el modal de Consumos)
    productos = Producto.objects.filter(activo=True, stock__gt=0).order_by('nombre')

    context = {
        'pisos': pisos,
        'piso_actual': piso_actual,
        'piso_sel': piso_actual.pk if piso_actual else None,
        'habitaciones': habitaciones,
        'productos': productos,
    }
    return render(request, 'Cristal_app/Recepcion/recepcion.html', context)

@login_required
def ocupar_habitacion(request, pk):
    hab = get_object_or_404(Habitacion, pk=pk)
    if hab.estado != "DISPONIBLE":
        messages.error(request, "La habitación no está disponible.")
        return redirect("recepcion")

    if request.method == "POST":
        rform = ReservaForm(request.POST)
        pform = PagoForm(request.POST)
        aformset = AcompananteFormSet(request.POST, prefix="acompanantes")

        if rform.is_valid() and pform.is_valid() and aformset.is_valid():
            with transaction.atomic():
                # 1) Reserva
                reserva = rform.save(commit=False)
                reserva.habitacion = hab
                reserva.estado = "ACTIVA"
                reserva.fecha_entrada = timezone.now()

                # calcular noches (al menos 1)
                delta = rform.cleaned_data["fecha_salida"] - reserva.fecha_entrada
                noches = delta.days + (1 if delta.seconds > 0 else 0)
                if noches <= 0:
                    noches = 1

                # costos
                precio_noche = Decimal(hab.precio_noche)
                reserva.costo_habitacion = precio_noche * noches
                reserva.costo_productos = Decimal("0.00")

                desc = Decimal(str(rform.cleaned_data.get("descuento_porcentaje") or 0))
                factor_desc = (Decimal("100.00") - desc) / Decimal("100.00")
                reserva.costo_total = (reserva.costo_habitacion * factor_desc).quantize(Decimal("0.01"))

                reserva.save()

                # 2) Pago
                pago = pform.save(commit=False)
                pago.reserva = reserva
                pago.save()

                # 3) Acompañantes
                aformset.instance = reserva
                aformset.save()

                # 4) Cambiar estado habitación
                hab.estado = "OCUPADA"
                hab.save()

            messages.success(request, f"Habitación {hab.numero} ocupada correctamente.")
            return redirect("recepcion")
        else:
            messages.error(request, "Revisa los datos del formulario.")
    else:
        # Inicializamos salida a +1 día
        salida_inicial = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        rform = ReservaForm(initial={"fecha_salida": salida_inicial})
        pform = PagoForm()
        aformset = AcompananteFormSet(prefix="acompanantes")

    return render(request, "Cristal_app/Recepcion/ocupar_form.html", {
        "habitacion": hab,
        "rform": rform,
        "pform": pform,
        "aformset": aformset,
    })

@login_required
def checkout_habitacion(request, pk):
    hab = get_object_or_404(Habitacion, pk=pk)
    reserva = Reserva.objects.filter(habitacion=hab, estado='ACTIVA').first()
    if not reserva:
        messages.error(request, 'No hay una reserva activa para esta habitación.')
        return redirect('recepcion')

    if request.method == 'POST':
        with transaction.atomic():
            reserva.estado = 'FINALIZADA'
            reserva.fecha_salida = timezone.now()
            reserva.save()
            hab.estado = 'LIMPIEZA'
            hab.save()
        messages.success(request, f'Checkout realizado. Habitación {hab.numero} en limpieza.')
        return redirect('recepcion')

    return render(request, 'Cristal_app/Recepcion/checkout_confirm.html', {'habitacion': hab, 'reserva': reserva})


@login_required
def marcar_limpieza(request, pk):
    hab = get_object_or_404(Habitacion, pk=pk)
    if hab.estado not in ('OCUPADA', 'DISPONIBLE'):
        messages.error(request, 'No se puede marcar limpieza desde el estado actual.')
        return redirect('recepcion')
    if request.method == 'POST':
        hab.estado = 'LIMPIEZA'
        hab.save()
        messages.success(request, f'Habitación {hab.numero} marcada para limpieza.')
        return redirect('recepcion')
    return render(request, 'Cristal_app/Recepcion/limpieza_confirm.html', {'habitacion': hab})


@login_required
def marcar_disponible(request, pk):
    hab = get_object_or_404(Habitacion, pk=pk)
    if hab.estado != 'LIMPIEZA':
        messages.error(request, 'Solo se puede marcar disponible desde limpieza.')
        return redirect('recepcion')
    if request.method == 'POST':
        hab.estado = 'DISPONIBLE'
        hab.save()
        messages.success(request, f'Habitación {hab.numero} disponible.')
        return redirect('recepcion')
    return render(request, 'Cristal_app/Recepcion/disponible_confirm.html', {'habitacion': hab})
@login_required
@require_POST
def registrar_consumo(request, habitacion_id):
    hab = get_object_or_404(Habitacion, pk=habitacion_id)
    reserva = get_object_or_404(Reserva, habitacion=hab, estado='ACTIVA')

    prod_ids = request.POST.getlist('producto_id[]')
    cantidades = request.POST.getlist('cantidad[]')

    next_url = request.POST.get('next') or reverse('recepcion')

    with transaction.atomic():
        # Crear o usar la venta asociada a la reserva
        venta = reserva.venta or Venta.objects.create(cliente=reserva.cliente, usuario=request.user)
        if reserva.venta_id is None:
            reserva.venta = venta
            reserva.save(update_fields=['venta'])

        total_lineas = 0
        for pid, cant in zip(prod_ids, cantidades):
            if not pid:
                continue
            p = get_object_or_404(Producto, pk=pid)
            c = max(int(cant or 1), 1)

            # Crear detalle de venta
            DetalleVenta.objects.create(
                venta=venta,
                producto=p,
                cantidad=c,
                precio_unitario=p.precio_venta
            )

            # Descontar stock
            p.stock = F('stock') - c
            p.save(update_fields=['stock'])

            total_lineas += float(p.precio_venta) * c

        # Actualizar total de la venta y de la reserva (costo_productos / costo_total)
        venta.total_venta = (venta.total_venta or 0) + total_lineas
        venta.save(update_fields=['total_venta'])

        reserva.costo_productos = (reserva.costo_productos or 0) + total_lineas
        # Si manejas costo_total, actualízalo aquí
        if reserva.costo_total is not None:
            reserva.costo_total = float(reserva.costo_total) + total_lineas
        reserva.save(update_fields=['costo_productos', 'costo_total'])

    return redirect(next_url)
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
class TipoHabitacionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TipoHabitacion
    template_name = 'Cristal_app/Mantenimiento/TipoHabitacion/tipohabitacion_list.html'
    context_object_name = 'tipohabitaciones'
    permission_required = 'Cristal_app.view_tipohabitacion'


class TipoHabitacionCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = TipoHabitacion
    fields = ['nombre', 'descripcion', 'activo']
    template_name = 'Cristal_app/Mantenimiento/TipoHabitacion/tipohabitacion_form.html'
    success_url = reverse_lazy('tipohabitacion_list')
    success_message = "Tipo de Habitación '%(nombre)s' creado exitosamente."
    permission_required = 'Cristal_app.add_tipohabitacion'


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


class HabitacionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Habitacion
    template_name = 'Cristal_app/Mantenimiento/Habitacion/habitacion_list.html'
    context_object_name = 'habitaciones'
    permission_required = 'Cristal_app.view_habitacion'


class HabitacionCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Habitacion
    fields = ['numero', 'piso', 'tipo', 'descripcion', 'precio_noche', 'activo']
    template_name = 'Cristal_app/Mantenimiento/Habitacion/habitacion_form.html'
    success_url = reverse_lazy('habitacion_list')
    success_message = "Habitación '%(numero)s' creada exitosamente."
    permission_required = 'Cristal_app.add_habitacion'


class HabitacionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Habitacion
    fields = ['numero', 'piso', 'tipo', 'descripcion', 'precio_noche', 'activo']
    template_name = 'Cristal_app/Mantenimiento/Habitacion/habitacion_form.html'
    success_url = reverse_lazy('habitacion_list')
    success_message = "Habitación '%(numero)s' actualizada exitosamente."
    permission_required = 'Cristal_app.change_habitacion'


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
