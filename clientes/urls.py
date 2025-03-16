from django.urls import path


from django.contrib.auth import views as auth_views
from .views import vencimientos_pagos
from .views import pago_cuota_enlinea, eliminar_comprobante, eliminar_comprobante, listar_comprobantes
from .views import listar_qr_clientes
from . import views

urlpatterns = [
    path('index', views.index, name='index'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),  # Redirige al home después de cerrar sesión
    path('registro/', views.registro_usuario, name='registro_usuario'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('perfil/', views.perfil, name='perfil'),
    path('editar_perfil/', views.editar_perfil, name='editar_perfil'),
    path('completar_perfil/', views.completar_perfil, name='completar_perfil'),
    path('', views.home, name='home'),
    path('clientes/', views.listar_clientes, name='listar_clientes'),
    path('clientes/nuevo/', views.crear_cliente, name='crear_cliente'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('eliminar_asistencia/<int:asistencia_id>/', views.eliminar_asistencia, name='eliminar_asistencia'),
    path('inactivos/', views.listar_inactivos, name='listar_inactivos'),

    path('asistencias/', views.listar_asistencias, name='listar_asistencias'),
    path('asistencias/nueva/', views.crear_asistencia, name='crear_asistencia'),
    path('asistencias/editar/<int:id>/', views.editar_asistencia, name='editar_asistencia'),
    path('pagos/', views.listar_pagos, name='listar_pagos'),
    path('pagos/nuevo/', views.crear_pago, name='crear_pago'),
    path('eliminar_pago/<int:id>/', views.eliminar_pago, name='eliminar_pago'),

    path('recaudacion/', views.recaudacion_view, name='recaudacion'),
    path('editar_pago/<int:id>/', views.editar_pago, name='editar_pago'),
    path('eliminar_nota/<int:nota_id>/', views.eliminar_nota, name='eliminar_nota'),
    path('editar/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    path('eliminar/<int:cliente_id>/', views.eliminar_cliente, name='eliminar_cliente'),
    path("escanear_qr/", views.escanear_qr, name="escanear_qr"),
    path('listar_qr/', listar_qr_clientes, name='listar_qr_clientes'),

    path('registrar_asistencia_qr/', views.registrar_asistencia_qr, name='registrar_asistencia_qr'),
    path('generar_qr/<int:cliente_id>/', views.generar_qr, name='generar_qr'),
    path('estado_cuota/<int:cliente_id>/', views.estado_cuota, name='estado_cuota'),
    path('vencimientos/', vencimientos_pagos, name='vencimientos_pagos'),
    
    path('listar_rutinas/', views.listar_rutinas, name='listar_rutinas'),
    
    path('pago_en_linea/', pago_cuota_enlinea, name='pago_cuota_enlinea'),
    
    path('eliminar_comprobante/<int:comprobante_id>/', eliminar_comprobante, name='eliminar_comprobante'),
    path('listar_comprobantes/', listar_comprobantes, name='listar_comprobantes'),
    path('listar-rutinas/', views.listar_rutinas, name='listar_rutinas'),
    path("mi-rutina/", views.mi_rutina, name="mi_rutina"),
    
    path('editar-rutina/<int:rutina_id>/', views.editar_rutina, name='editar_rutina'),
    path('crear_rutina/', views.crear_rutina, name='crear_rutina'),
    path("asignar_cliente_a_rutina/<int:rutina_id>/", views.asignar_cliente_a_rutina, name="asignar_cliente_a_rutina"),
    path('eliminar-todos-clientes-de-rutina/<int:rutina_id>/', views.eliminar_todos_clientes_de_rutina, name='eliminar_todos_clientes_de_rutina'),
    path('eliminar_cliente_de_rutina/<int:rutina_id>/<int:cliente_id>/', views.eliminar_cliente_de_rutina, name='eliminar_cliente_de_rutina'),
    path('eliminar_grupo/<int:grupo_id>/', views.eliminar_grupo, name='eliminar_grupo'),
    path('eliminar_subgrupo/<int:subgrupo_id>/', views.eliminar_subgrupo, name='eliminar_subgrupo'),
    # nutricion
    path('listar-planes-nutricionales/', views.listar_planes_nutricionales, name='listar_planes_nutricionales'),
    path("mi-plan-nutricional/", views.mi_plan_nutricional, name="mi_plan_nutricional"),
    
    path('editar-plan-nutricional/<int:plan_nutricional_id>/', views.editar_plan_nutricional, name='editar_plan_nutricional'),
    path('crear-plan-nutricional/', views.crear_plan_nutricional, name='crear_plan_nutricional'),
    path("asignar_cliente_a_plan_nutricional/<int:plan_nutricional_id>/", views.asignar_cliente_a_plan_nutricional, name="asignar_cliente_a_plan_nutricional"),
    path('eliminar-todos-clientes-de-plan-nutricional/<int:plan_nutricional_id>/', views.eliminar_todos_clientes_de_plan_nutricional, name='eliminar_todos_clientes_de_plan_nutricional'),
    path('eliminar_cliente_de_plan_nutricional/<int:plan_nutricional_id>/<int:cliente_id>/', views.eliminar_cliente_de_plan_nutricional, name='eliminar_cliente_de_plan_nutricional'),
    path('eliminar_categoria/<int:id>/', views.eliminar_categoria, name='eliminar_categoria'),
    path('eliminar_subcategoria/<int:subcategoria_id>/', views.eliminar_subcategoria, name='eliminar_subcategoria'),
    path('eliminar_cliente_de_plan/<int:plan_id>/<int:cliente_id>/', views.eliminar_cliente_de_plan, name='eliminar_cliente_de_plan'),

]