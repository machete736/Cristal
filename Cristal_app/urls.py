from django.urls import path
from . import views  # Asegúrate de importar las vistas

urlpatterns = [
    # Home
    path('', views.home_view, name='home'),

    # RECEPCIÓN
    path('recepcion/', views.recepcion_view, name='recepcion'),
    path('recepcion/ocupar/<int:pk>/', views.ocupar_habitacion, name='ocupar_habitacion'),
    path('recepcion/checkout/<int:pk>/', views.checkout_habitacion, name='checkout_habitacion'),
    path('recepcion/consumo/<int:habitacion_id>/', views.registrar_consumo, name='registrar_consumo'),
    path('recepcion/limpieza/<int:pk>/', views.marcar_limpieza, name='marcar_limpieza'),
    path('recepcion/disponible/<int:pk>/', views.marcar_disponible, name='marcar_disponible'),

    # Ruta faltante para ver detalles de la reserva
    path('recepcion/detalles_reserva/<int:reserva_id>/', views.ver_detalles_reserva, name='ver_detalles_reserva'),

    # CRUD Usuarios
    path('usuarios/', views.UserListView.as_view(), name='user_list'),
    path('usuarios/crear/', views.UserCreateView.as_view(), name='user_create'),
    path('usuarios/editar/<int:pk>/', views.UserUpdateView.as_view(), name='user_update'),
    path('usuarios/eliminar/<int:pk>/', views.UserDeleteView.as_view(), name='user_delete'),

    # CRUD Roles
    path('roles/', views.GroupListView.as_view(), name='group_list'),
    path('roles/crear/', views.GroupCreateView.as_view(), name='group_create'),
    path('roles/editar/<int:pk>/', views.GroupUpdateView.as_view(), name='group_update'),
    path('roles/eliminar/<int:pk>/', views.GroupDeleteView.as_view(), name='group_delete'),

    # CRUD Almacén
    path('proveedores/', views.ProveedorListView.as_view(), name='proveedor_list'),
    path('proveedores/crear/', views.ProveedorCreateView.as_view(), name='proveedor_create'),
    path('proveedores/editar/<int:pk>/', views.ProveedorUpdateView.as_view(), name='proveedor_update'),
    path('proveedores/eliminar/<int:pk>/', views.ProveedorDeleteView.as_view(), name='proveedor_delete'),

    path('categorias/', views.CategoriaListView.as_view(), name='categoria_list'),
    path('categorias/crear/', views.CategoriaCreateView.as_view(), name='categoria_create'),
    path('categorias/editar/<int:pk>/', views.CategoriaUpdateView.as_view(), name='categoria_update'),
    path('categorias/eliminar/<int:pk>/', views.CategoriaDeleteView.as_view(), name='categoria_delete'),

    path('productos/', views.ProductoListView.as_view(), name='producto_list'),
    path('productos/crear/', views.ProductoCreateView.as_view(), name='producto_create'),
    path('productos/editar/<int:pk>/', views.ProductoUpdateView.as_view(), name='producto_update'),
    path('productos/eliminar/<int:pk>/', views.ProductoDeleteView.as_view(), name='producto_delete'),

    # CRUD Compras
    path('compras/', views.CompraListView.as_view(), name='compra_list'),
    path('compras/crear/', views.CompraCreateView.as_view(), name='compra_create'),
    path('compras/editar/<int:pk>/', views.CompraUpdateView.as_view(), name='compra_update'),
    path('compras/eliminar/<int:pk>/', views.CompraDeleteView.as_view(), name='compra_delete'),

    # CRUD Ventas
    path('ventas/', views.VentaListView.as_view(), name='venta_list'),
    path('ventas/crear/', views.VentaCreateView.as_view(), name='venta_create'),
    path('ventas/editar/<int:pk>/', views.VentaUpdateView.as_view(), name='venta_update'),
    path('ventas/eliminar/<int:pk>/', views.VentaDeleteView.as_view(), name='venta_delete'),

    # CRUD Clientes
    path('clientes/', views.ClienteListView.as_view(), name='cliente_list'),
    path('clientes/crear/', views.ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/editar/<int:pk>/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/eliminar/<int:pk>/', views.ClienteDeleteView.as_view(), name='cliente_delete'),
    # URL para la creación de clientes vía AJAX
    path('clientes/crear/ajax/', views.crear_cliente_ajax, name='crear_cliente_ajax'),

    # CRUD Clientes (estas ya las tienes)
    path('clientes/', views.ClienteListView.as_view(), name='cliente_list'),
    # ...

    # Rutas para gestionar tarifas
    path('tipohabitacion/<int:pk>/tarifas/', views.gestionar_tarifas, name='gestionar_tarifas'),
    path('tarifa/nueva/<int:tipo_id>/', views.editar_tarifa, name='crear_tarifa'),
    path('tarifa/<int:pk>/editar/', views.editar_tarifa, name='editar_tarifa'),
    path('tarifa/<int:pk>/eliminar/', views.eliminar_tarifa, name='eliminar_tarifa'),
    path('api/tipohabitacion/<int:tipo_id>/tarifas/', views.obtener_tarifas, name='obtener_tarifas'),


    # CRUD Mantenimiento > TipoHabitacion
    path('mantenimiento/tipohabitacion/', views.TipoHabitacionListView.as_view(), name='tipohabitacion_list'),
    path('mantenimiento/tipohabitacion/crear/', views.TipoHabitacionCreateView.as_view(), name='tipohabitacion_create'),
    path('mantenimiento/tipohabitacion/editar/<int:pk>/', views.TipoHabitacionUpdateView.as_view(), name='tipohabitacion_update'),
    path('mantenimiento/tipohabitacion/eliminar/<int:pk>/', views.TipoHabitacionDeleteView.as_view(), name='tipohabitacion_delete'),

    # CRUD Mantenimiento > Pisos
    path('mantenimiento/pisos/', views.PisoListView.as_view(), name='piso_list'),
    path('mantenimiento/pisos/crear/', views.PisoCreateView.as_view(), name='piso_create'),
    path('mantenimiento/pisos/editar/<int:pk>/', views.PisoUpdateView.as_view(), name='piso_update'),
    path('mantenimiento/pisos/eliminar/<int:pk>/', views.PisoDeleteView.as_view(), name='piso_delete'),

    # CRUD Mantenimiento > Habitaciones
    path('habitaciones/', views.HabitacionListView.as_view(), name='habitacion_list'),
    path('habitaciones/nueva/', views.HabitacionCreateView.as_view(), name='habitacion_create'),
    path('habitaciones/editar/<int:pk>/', views.HabitacionUpdateView.as_view(), name='habitacion_update'),
    path('habitaciones/eliminar/<int:pk>/', views.HabitacionDeleteView.as_view(), name='habitacion_delete'),
    #tipopago
    path('tipopago/', views.tipo_pago_list, name='tipopago_list'),
    path('tipopago/create/', views.tipo_pago_create_or_update, name='tipopago_create'),
    path('tipopago/update/<int:pk>/', views.tipo_pago_create_or_update, name='tipopago_update'),
    path('tipopago/delete/<int:pk>/', views.tipo_pago_delete, name='tipopago_delete'),
    #reportes
    path('reportes/reservas/', views.reporte_reservas, name='reporte_reservas'),
    path('reportes/consumos/', views.reporte_consumos, name='reporte_consumos'),
    path('reportes/habitaciones-ocupadas/', views.reporte_habitaciones_ocupadas, name='reporte_habitaciones_ocupadas'),
    path('reportes/ingresos/', views.reporte_ingresos, name='reporte_ingresos'),
    # URL para generar el PDF
    path('reportes/reservas/pdf/', views.generar_pdf, name='generar_pdf'),
    # URL para ver el reporte de ingresos en la página
    path('reportes/ingresos/', views.reporte_ingresos, name='reporte_ingresos'),

    # URL para generar el PDF del reporte de ingresos
    path('reportes/ingresos/pdf/', views.generar_pdf_ingresos, name='generar_pdf_ingresos'),
    path('reportes/resumen/', views.reporte_resumen, name='reporte_resumen'),
    path('reportes/resumen/pdf/', views.generar_pdf_resumen, name='generar_pdf_resumen'),

]