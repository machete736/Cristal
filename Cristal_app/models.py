# Cristal_app/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

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
class Piso(models.Model):
    numero = models.PositiveIntegerField(unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Piso {self.numero}"


class TipoHabitacion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Habitacion(models.Model):
    ESTADO_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('OCUPADA', 'Ocupada'),
        ('LIMPIEZA', 'Limpieza'),
    ]
    numero = models.CharField(max_length=10, unique=True)
    piso = models.ForeignKey(Piso, on_delete=models.CASCADE, related_name='habitaciones')
    tipo = models.ForeignKey(TipoHabitacion, on_delete=models.SET_NULL, null=True, related_name='habitaciones')
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    precio_noche = models.DecimalField(max_digits=8, decimal_places=2)
    activo = models.BooleanField(default=True)
    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES, default='DISPONIBLE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Habitación {self.numero}"


# -------------------------
# RECEPCIÓN / RESERVAS
# -------------------------
class Reserva(models.Model):
    ESTADO_RESERVA_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('ACTIVA', 'Activa'),
        ('FINALIZADA', 'Finalizada'),
        ('CANCELADA', 'Cancelada'),
    ]

    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE, related_name='reservas')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='reservas')

    # Entrada se fija al registrar; salida la edita el operador
    fecha_entrada = models.DateTimeField(default=timezone.now)
    fecha_salida  = models.DateTimeField()

    estado = models.CharField(max_length=15, choices=ESTADO_RESERVA_CHOICES, default='PENDIENTE')

    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)

    costo_habitacion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_productos  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_total      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    venta = models.OneToOneField(Venta, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='reserva_asociada')

    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reserva de {self.cliente.nombrecompleto} para la Hab. {self.habitacion.numero}"

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"


class Acompanante(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='acompanantes')
    nombre_completo = models.CharField(max_length=255)
    dni = models.CharField(max_length=8)

    def __str__(self):
        return self.nombre_completo

    class Meta:
        verbose_name = "Acompañante"
        verbose_name_plural = "Acompañantes"


class TipoPago(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Tipo de Pago"
        verbose_name_plural = "Tipos de Pagos"


class Pago(models.Model):
    """Un pago simple por reserva (si luego quieres pagos parciales, cambia a ForeignKey)."""
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='pago')
    tipo_pago = models.ForeignKey(TipoPago, on_delete=models.SET_NULL, null=True)
    monto_recibido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    comprobante_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Pago de Reserva #{self.reserva.pk}"

    class Meta:
        verbose_name = "Pago de Reserva"
        verbose_name_plural = "Pagos de Reservas"
