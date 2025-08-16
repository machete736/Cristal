# Cristal_app/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
# -------------------------
# USUARIOS
# -------------------------
class CustomUser(AbstractUser):
    """No vuelvas a redefinir groups/user_permissions; ya vienen en AbstractUser."""
    pass


# -------------------------
# CLIENTES
# -------------------------
class Cliente(models.Model):
    dni = models.CharField(max_length=8, unique=True)
    nombrecompleto = models.CharField(max_length=255)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.nombrecompleto

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


# -------------------------
# ALMACÉN
# -------------------------
class Proveedor(models.Model):
    nombre = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"


class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"


class Producto(models.Model):
    nombre = models.CharField(max_length=255)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"


class Compra(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    fecha_compra = models.DateTimeField(auto_now_add=True)
    total_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Compra #{self.pk} - {self.proveedor.nombre}"

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"


class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle de Compra #{self.compra.pk}"

    @property
    def subtotal(self):
        return self.cantidad * self.costo_unitario

    class Meta:
        verbose_name = "Detalle de Compra"
        verbose_name_plural = "Detalles de Compras"


class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True)
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    fecha_venta = models.DateTimeField(auto_now_add=True)
    total_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        c = self.cliente.nombrecompleto if self.cliente else 'Sin cliente'
        return f"Venta #{self.pk} - {c}"

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Detalle de Venta #{self.venta.pk}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Ventas"


# -------------------------
# MANTENIMIENTO / HOTEL
# -------------------------

class TipoHabitacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    @property
    def tiene_tarifas(self):
        return self.tarifas.exists()

    def __str__(self):
        return self.nombre


class Tarifa(models.Model):
    """
    Tarifa genérica por TIPO DE HABITACIÓN.
    Con esto puedes crear, por ejemplo:
      - tipo='DÍA',  nombre='NOCHE',    duracion=1, precio=35.00  -> “D - NOCHE (35.00)”
      - tipo='HORA', nombre='HORA (4)', duracion=4, precio=25.00  -> “P HORA (4) (25.00)”
      - tipo='HORA', nombre='6 HORAS',  duracion=6, precio=28.00
    """
    TIPO_CHOICES = (('HORA', 'Hora'), ('DÍA', 'Día'), ('SEMANA', 'Semana'))
    tipo_habitacion = models.ForeignKey(TipoHabitacion, on_delete=models.CASCADE, related_name='tarifas')
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    duracion = models.PositiveIntegerField(help_text="Horas si es HORA, días si es DÍA o SEMANA")
    precio = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        # Ej: “D - NOCHE (35.00)”
        pref = self.tipo[0]
        return f"{pref} - {self.nombre} ({self.precio:.2f})"

    class Meta:
        verbose_name = "Tarifa"
        verbose_name_plural = "Tarifas"


class Piso(models.Model):
    numero = models.PositiveIntegerField(unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Piso {self.numero}"


class TipoPago(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    activo = models.BooleanField(default=True)  # <-- lo usa tu CRUD
    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Tipo de Pago"
        verbose_name_plural = "Tipos de Pagos"


class Habitacion(models.Model):
    ESTADO_CHOICES = (('DISPONIBLE', 'Disponible'), ('OCUPADA', 'Ocupada'), ('LIMPIEZA', 'Limpieza'))
    numero = models.CharField(max_length=10, unique=True)
    piso = models.ForeignKey(Piso, on_delete=models.CASCADE, related_name='habitaciones')
    tipo = models.ForeignKey(TipoHabitacion, on_delete=models.SET_NULL, null=True, related_name='habitaciones')
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    activo = models.BooleanField(default=True)
    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES, default='DISPONIBLE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Habitación {self.numero}"

    # --- NUEVO: usado por tu template “Precio Noche” ---
    @property
    def precio_noche(self) -> Decimal:
        """
        Devuelve el precio de la tarifa 'noche' más barata del tipo de esta habitación.
        Evita que el template truene si no existe el campo.
        """
        if not self.tipo:
            return Decimal('0.00')
        t = (self.tipo.tarifas
             .filter(tipo='DÍA')
             .order_by('precio'))
        if not t.exists():
            return Decimal('0.00')
        return t.first().precio

    # --- NUEVO: accesible como habitacion.reserva_activa ---
    @property
    def reserva_activa(self):
        return self.reservas.filter(estado='ACTIVA').order_by('-fecha_entrada').first()


# -------------------------
# RECEPCIÓN / RESERVAS
# -------------------------

class Reserva(models.Model):
    ESTADO_RESERVA_CHOICES = (('PENDIENTE', 'Pendiente'),
                              ('ACTIVA', 'Activa'),
                              ('FINALIZADA', 'Finalizada'),
                              ('CANCELADA', 'Cancelada'))

    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE, related_name='reservas')
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, related_name='reservas')

    # Snapshot de la tarifa elegida en la ocupación
    tarifa = models.ForeignKey(Tarifa, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservas')
    unidades_tarifa = models.PositiveIntegerField(default=1, help_text="p.ej., 1 noche, 2 noches, etc.")

    fecha_entrada = models.DateTimeField(default=timezone.now)
    fecha_salida = models.DateTimeField()

    estado = models.CharField(max_length=15, choices=ESTADO_RESERVA_CHOICES, default='PENDIENTE')

    # Descuentos (la UI muestra monto en Bs.)
    descuento_monto = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))

    # Costos
    costo_habitacion = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    costo_productos = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    costo_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    venta = models.OneToOneField('Venta', on_delete=models.SET_NULL, null=True, blank=True, related_name='reserva_asociada')

    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reserva Hab {self.habitacion.numero} - {self.cliente.nombrecompleto}"

    # ----- Cálculos -----
    def _calc_costo_habitacion(self) -> Decimal:
        if not self.tarifa_id:
            return Decimal('0.00')
        return (self.tarifa.precio or Decimal('0.00')) * self.unidades_tarifa

    def _calc_fecha_salida_por_tarifa(self):
        if not (self.fecha_entrada and self.tarifa_id):
            return
        dur = self.tarifa.duracion * self.unidades_tarifa
        if self.tarifa.tipo == 'HORA':
            self.fecha_salida = self.fecha_entrada + timedelta(hours=dur)
        elif self.tarifa.tipo == 'DÍA':
            self.fecha_salida = self.fecha_entrada + timedelta(days=dur)
        elif self.tarifa.tipo == 'SEMANA':
            self.fecha_salida = self.fecha_entrada + timedelta(days=7 * self.unidades_tarifa)

    def _calc_totales(self):
        self.costo_habitacion = self._calc_costo_habitacion()
        subtotal = (self.costo_habitacion or Decimal('0.00')) + (self.costo_productos or Decimal('0.00'))
        # si te pasan ambos descuentos, se suman
        desc = (self.descuento_monto or Decimal('0.00')) + (subtotal * (self.descuento_porcentaje or 0) / Decimal('100'))
        self.costo_total = subtotal - desc

    def save(self, *args, **kwargs):
        # fecha_salida automática según la tarifa seleccionada
        if self.tarifa_id and not self.fecha_salida:
            self._calc_fecha_salida_por_tarifa()
        # totales
        self._calc_totales()
        super().save(*args, **kwargs)

    # Totales que pide la UI
    @property
    def total_pagado(self) -> Decimal:
        try:
            return self.pago.monto_recibido or Decimal('0.00')
        except (AttributeError, models.ObjectDoesNotExist):
            return Decimal('0.00')

    @property
    def deuda(self) -> Decimal:
        return (self.costo_total or Decimal('0.00')) - self.total_pagado


class Acompanante(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='acompanantes')
    nombre_completo = models.CharField(max_length=255)
    dni = models.CharField(max_length=8)

    def __str__(self):
        return self.nombre_completo


class Pago(models.Model):
    # Un pago por reserva (si luego quieres parciales, cambia a FK)
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='pago')
    tipo_pago = models.ForeignKey(TipoPago, on_delete=models.SET_NULL, null=True)
    monto_recibido = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    fecha_pago = models.DateTimeField(auto_now_add=True)
    comprobante_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Pago de Reserva #{self.reserva_id}"


class Consumo(models.Model):
    # Field to link to a related model, e.g., a Venta or a Reserva
    venta = models.ForeignKey('Venta', on_delete=models.CASCADE, null=True, blank=True)
    # If Consumo is linked directly to a client
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, null=True, blank=True)

    # The actual amount of the consumption
    monto_consumo = models.DecimalField(max_digits=10, decimal_places=2)

    # Date of the consumption
    fecha = models.DateTimeField(auto_now_add=True)

    # Description of the item consumed
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Consumo de {self.monto_consumo} el {self.fecha.date()}"