from django.urls import path

from .views import (
    home_view,
    registrar_consumo,
    # Vistas de Recepción
    recepcion_view,
    ocupar_habitacion,
    checkout_habitacion,
    marcar_limpieza,
    marcar_disponible,
    # Usuarios
    UserListView, UserCreateView, UserUpdateView, UserDeleteView,
    # Roles
    GroupListView, GroupCreateView, GroupUpdateView, GroupDeleteView,
    # Almacén
    ProveedorListView, ProveedorCreateView, ProveedorUpdateView, ProveedorDeleteView,
    CategoriaListView, CategoriaCreateView, CategoriaUpdateView, CategoriaDeleteView,
    ProductoListView, ProductoCreateView, ProductoUpdateView, ProductoDeleteView,
    # Compras/Ventas
    CompraListView, CompraCreateView, CompraUpdateView, CompraDeleteView,
    VentaListView, VentaCreateView, VentaUpdateView, VentaDeleteView,
    # Clientes
    ClienteListView, ClienteCreateView, ClienteUpdateView, ClienteDeleteView,
    # Mantenimiento
    TipoHabitacionListView, TipoHabitacionCreateView, TipoHabitacionUpdateView, TipoHabitacionDeleteView,
    PisoListView, PisoCreateView, PisoUpdateView, PisoDeleteView,
    HabitacionListView, HabitacionCreateView, HabitacionUpdateView, HabitacionDeleteView,
)

urlpatterns = [
    # Home
    path('', home_view, name='home'),

    # RECEPCIÓN
    path('recepcion/', recepcion_view, name='recepcion'),

    # Consumos (desde la recepción)
    path('recepcion/<int:habitacion_id>/consumos/', registrar_consumo, name='registrar_consumo'),

    path('recepcion/ocupar/<int:pk>/', ocupar_habitacion, name='ocupar_habitacion'),
    path('recepcion/checkout/<int:pk>/', checkout_habitacion, name='checkout_habitacion'),
    path('recepcion/limpieza/<int:pk>/', marcar_limpieza, name='marcar_limpieza'),
    path('recepcion/disponible/<int:pk>/', marcar_disponible, name='marcar_disponible'),

    # CRUD Usuarios
    path('usuarios/',       UserListView.as_view(),   name='user_list'),
    path('usuarios/crear/', UserCreateView.as_view(), name='user_create'),
    path('usuarios/editar/<int:pk>/',   UserUpdateView.as_view(), name='user_update'),
    path('usuarios/eliminar/<int:pk>/', UserDeleteView.as_view(), name='user_delete'),

    # CRUD Roles
    path('roles/',         GroupListView.as_view(),   name='group_list'),
    path('roles/crear/',   GroupCreateView.as_view(), name='group_create'),
    path('roles/editar/<int:pk>/',   GroupUpdateView.as_view(), name='group_update'),
    path('roles/eliminar/<int:pk>/', GroupDeleteView.as_view(), name='group_delete'),

    # CRUD Almacén
    path('proveedores/',        ProveedorListView.as_view(),   name='proveedor_list'),
    path('proveedores/crear/',  ProveedorCreateView.as_view(), name='proveedor_create'),
    path('proveedores/editar/<int:pk>/',   ProveedorUpdateView.as_view(), name='proveedor_update'),
    path('proveedores/eliminar/<int:pk>/', ProveedorDeleteView.as_view(), name='proveedor_delete'),

    path('categorias/',        CategoriaListView.as_view(),   name='categoria_list'),
    path('categorias/crear/',  CategoriaCreateView.as_view(), name='categoria_create'),
    path('categorias/editar/<int:pk>/',   CategoriaUpdateView.as_view(), name='categoria_update'),
    path('categorias/eliminar/<int:pk>/', CategoriaDeleteView.as_view(), name='categoria_delete'),

    path('productos/',        ProductoListView.as_view(),   name='producto_list'),
    path('productos/crear/',  ProductoCreateView.as_view(), name='producto_create'),
    path('productos/editar/<int:pk>/',   ProductoUpdateView.as_view(), name='producto_update'),
    path('productos/eliminar/<int:pk>/', ProductoDeleteView.as_view(), name='producto_delete'),

    # CRUD Compras
    path('compras/',            CompraListView.as_view(),   name='compra_list'),
    path('compras/crear/',      CompraCreateView.as_view(), name='compra_create'),
    path('compras/editar/<int:pk>/',   CompraUpdateView.as_view(), name='compra_update'),
    path('compras/eliminar/<int:pk>/', CompraDeleteView.as_view(), name='compra_delete'),

    # CRUD Ventas
    path('ventas/',            VentaListView.as_view(),   name='venta_list'),
    path('ventas/crear/',      VentaCreateView.as_view(), name='venta_create'),
    path('ventas/editar/<int:pk>/',   VentaUpdateView.as_view(), name='venta_update'),
    path('ventas/eliminar/<int:pk>/', VentaDeleteView.as_view(), name='venta_delete'),

    # CRUD Clientes
    path('clientes/',            ClienteListView.as_view(),   name='cliente_list'),
    path('clientes/crear/',      ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/editar/<int:pk>/',   ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/eliminar/<int:pk>/', ClienteDeleteView.as_view(), name='cliente_delete'),

    # CRUD Mantenimiento > TipoHabitacion
    path('mantenimiento/tipohabitacion/', TipoHabitacionListView.as_view(), name='tipohabitacion_list'),
    path('mantenimiento/tipohabitacion/crear/',  TipoHabitacionCreateView.as_view(), name='tipohabitacion_create'),
    path('mantenimiento/tipohabitacion/editar/<int:pk>/',   TipoHabitacionUpdateView.as_view(), name='tipohabitacion_update'),
    path('mantenimiento/tipohabitacion/eliminar/<int:pk>/', TipoHabitacionDeleteView.as_view(), name='tipohabitacion_delete'),

    # CRUD Mantenimiento > Pisos
    path('mantenimiento/pisos/',       PisoListView.as_view(),   name='piso_list'),
    path('mantenimiento/pisos/crear/', PisoCreateView.as_view(), name='piso_create'),
    path('mantenimiento/pisos/editar/<int:pk>/',   PisoUpdateView.as_view(), name='piso_update'),
    path('mantenimiento/pisos/eliminar/<int:pk>/', PisoDeleteView.as_view(), name='piso_delete'),

    # CRUD Mantenimiento > Habitaciones
    path('mantenimiento/habitaciones/',        HabitacionListView.as_view(),   name='habitacion_list'),
    path('mantenimiento/habitaciones/crear/',  HabitacionCreateView.as_view(), name='habitacion_create'),
    path('mantenimiento/habitaciones/editar/<int:pk>/',   HabitacionUpdateView.as_view(), name='habitacion_update'),
    path('mantenimiento/habitaciones/eliminar/<int:pk>/', HabitacionDeleteView.as_view(), name='habitacion_delete'),
]