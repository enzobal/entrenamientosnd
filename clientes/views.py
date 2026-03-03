
from .models import Cliente, Asistencia, Pago
from django.core.mail import send_mail
from django.conf import settings

from .forms import ClienteForm, AsistenciaForm, PagoForm
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test

from django.shortcuts import render, redirect, get_object_or_404


from django.contrib.auth.forms import UserCreationForm
from datetime import datetime

from .forms import RegistroUsuarioForm
from django.contrib import messages


def index(request):
    return render(request, 'index.html')

from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

def registro_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)

        # 🔥 Validamos si el username ya existe
        username = request.POST.get('username')
        if User.objects.filter(username=username).exists():
            return render(request, 'clientes/usuario_existente.html')

        if form.is_valid():
            form.save()
            messages.success(request, "Registro exitoso. ¡Ahora puedes iniciar sesión!")
            return redirect('home')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'clientes/registro_usuario.html', {'form': form})


from django.utils.timezone import now




@login_required
def home(request):
    ultimo_pago = None
    estado_pago = "Desconocido"
    cliente = None
    cumpleanieros = []  # NUEVO: lista para cumpleaños

    try:
        cliente = get_object_or_404(Cliente, user=request.user)
        ultimo_pago = Pago.objects.filter(cliente=cliente).order_by('-fecha_pago').first()

        if ultimo_pago:
            if ultimo_pago.fecha_fin and ultimo_pago.fecha_fin >= now().date():
                estado_pago = "Al día ✅"
            else:
                estado_pago = "Vencido ❌"
    except Cliente.DoesNotExist:
        estado_pago = "No registrado como cliente ❌"

    # 🔥 Buscar quienes cumplen años HOY
    hoy = date.today()
    cumpleanieros = Cliente.objects.filter(
        fecha_nacimiento__month=hoy.month,
        fecha_nacimiento__day=hoy.day
    )

    return render(request, 'clientes/home.html', {
        'cliente': cliente,
        'ultimo_pago': ultimo_pago,
        'estado_pago': estado_pago,
        'cumpleanieros': cumpleanieros,  # 🔥 Pasarlo al template
    })



# perfildel usuario






@login_required
def perfil(request):
    try:
        cliente = Cliente.objects.get(user=request.user)
    except Cliente.DoesNotExist:
        return redirect('completar_perfil')  # Redirigir a una vista para completar el perfil

    return render(request, 'clientes/perfil.html', {'cliente': cliente})



# para editar el perfil
from django.shortcuts import render, redirect



@login_required
def editar_perfil(request, cliente_id=None):
    """
    Permite editar el perfil del cliente.
    - Los usuarios solo pueden editar su propio perfil.
    - Los administradores pueden editar el perfil de cualquier cliente.
    """
    if cliente_id and request.user.is_staff:
        cliente = Cliente.objects.get(id=cliente_id)
    else:
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            cliente = Cliente(user=request.user)  # Crear un nuevo Cliente si no existe

    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('listar_clientes' if request.user.is_staff else 'perfil')
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'clientes/editar_perfil.html', {'form': form})


from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClienteForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Cliente
from .forms import ClienteForm, UserEditForm, PasswordChangeCustomForm


@login_required
def editar_cliente(request, cliente_id=None):
    """
    Permite al administrador editar cualquier cliente.
    Los usuarios normales solo pueden editar su propio perfil.
    Además permite editar los datos del usuario (nombre, apellido, email, username)
    y cambiar la contraseña de forma segura.
    """
    # --- Determinar el cliente a editar ---
    if cliente_id and request.user.is_staff:  # Si es admin y se pasa un cliente_id
        cliente = get_object_or_404(Cliente, id=cliente_id)
        usuario = cliente.user
    elif not cliente_id:  # Usuario común editando su perfil
        try:
            cliente = request.user.cliente
            usuario = request.user
        except Cliente.DoesNotExist:
            messages.error(request, "No se encontró el perfil del cliente.")
            return redirect('perfil')
    else:  # Si no es admin y trata de editar otro cliente
        messages.warning(request, "No tienes permisos para editar este cliente.")
        return redirect('perfil')

    # --- Procesamiento del formulario ---
    if request.method == 'POST':
        cliente_form = ClienteForm(request.POST, request.FILES, instance=cliente)
        user_form = UserEditForm(request.POST, instance=usuario)
        password_form = PasswordChangeCustomForm(request.POST)

        if cliente_form.is_valid() and user_form.is_valid() and password_form.is_valid():
            # Guardar cambios del cliente y usuario
            cliente_form.save()
            user_form.save()

            # --- Manejo del cambio de contraseña ---
            nueva_pass = password_form.cleaned_data.get('nueva_password')
            pass_actual = password_form.cleaned_data.get('password_actual')

            if nueva_pass:
                if usuario.check_password(pass_actual):
                    try:
                        validate_password(nueva_pass, usuario)
                        usuario.set_password(nueva_pass)
                        usuario.save()
                        update_session_auth_hash(request, usuario)
                        messages.success(request, "🔒 Contraseña actualizada correctamente.")
                    except ValidationError as e:
                        messages.error(request, f"Error al validar la contraseña: {e}")
                        return redirect('editar_cliente', cliente_id=cliente.id if request.user.is_staff else None)
                else:
                    messages.error(request, "⚠️ La contraseña actual no es correcta.")
                    return redirect('editar_cliente', cliente_id=cliente.id if request.user.is_staff else None)

            messages.success(request, "✅ Perfil actualizado correctamente.")
            return redirect('listar_clientes' if request.user.is_staff else 'perfil')
        else:
            messages.error(request, "⚠️ Verifica los datos ingresados.")
    else:
        cliente_form = ClienteForm(instance=cliente)
        user_form = UserEditForm(instance=usuario)
        password_form = PasswordChangeCustomForm()

    # --- Renderizar template ---
    return render(request, 'clientes/editar_cliente.html', {
        'form': cliente_form,
        'user_form': user_form,
        'password_form': password_form,
        'cliente': cliente
    })






# cpmpletar el perfil si no lo tiene
from django.shortcuts import render, redirect
from .forms import ClienteForm  # Asumiendo que tienes un formulario para el modelo Cliente


@login_required
def completar_perfil(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.user = request.user
            cliente.save()

            # Enviar el saludo al correo
            if cliente.email:  # Asegurarse de que haya un correo
                send_mail(
                    subject='¡Bienvenido a nuestro gimnasio!',
                    message=f'Hola {cliente.nombre},\n\n¡Gracias por completar tu perfil! Estamos muy felices de tenerte con nosotros.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[cliente.email],
                    fail_silently=False,
                )

            return redirect('perfil')
    else:
        form = ClienteForm()

    return render(request, 'clientes/completar_perfil.html', {'form': form})










@login_required
def listar_clientes(request):
    if request.user.is_staff:
        clientes = Cliente.objects.all()
    else:
        clientes = Cliente.objects.filter(user=request.user)

    # Calcular estado de membresía para cada cliente
    for cliente in clientes:
        cliente.membresia_vencida = cliente.membresia_vencida()

    return render(request, 'clientes/listar_clientes.html', {'clientes': clientes})

from django.shortcuts import render
from django.db.models import Subquery, Exists, OuterRef, Q, DateField
from django.utils.timezone import now
from datetime import timedelta

from .models import Cliente, Asistencia, Pago

def listar_inactivos(request):
    hoy = now().date()
    hace_un_mes = hoy - timedelta(days=30)

    # Subconsulta para última asistencia presente
    subquery_ultima_asistencia = Asistencia.objects.filter(
        cliente=OuterRef('pk'),
        presente=True
    ).order_by('-fecha').values('fecha')[:1]

    # Subconsulta para último pago vigente (fecha_inicio <= hoy <= fecha_fin)
    subquery_pago_vigente = Pago.objects.filter(
        cliente=OuterRef('pk'),
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy
    )

    # Subconsulta para obtener última fecha de pago (por si no tiene vigente)
    subquery_ultimo_pago = Pago.objects.filter(
        cliente=OuterRef('pk')
    ).order_by('-fecha_fin').values('fecha_fin')[:1]

    # Anotaciones
    clientes = Cliente.objects.annotate(
        ultima_asistencia=Subquery(subquery_ultima_asistencia, output_field=DateField()),
        tiene_pago_vigente=Exists(subquery_pago_vigente),
        fecha_ultimo_pago=Subquery(subquery_ultimo_pago, output_field=DateField())
    )

    # Filtrar clientes inactivos
    clientes_inactivos = []
    for cliente in clientes:
        motivo = []

        # Verificación de cuota
        if not cliente.tiene_pago_vigente:
            if cliente.fecha_ultimo_pago:
                dias_sin_cuota = (hoy - cliente.fecha_ultimo_pago).days
                motivo.append(f"No tiene cuota vigente desde hace {dias_sin_cuota} días")
            else:
                motivo.append("Nunca pagó una cuota")

        # Verificación de asistencia
        if not cliente.ultima_asistencia or cliente.ultima_asistencia < hace_un_mes:
            dias = (hoy - cliente.ultima_asistencia).days if cliente.ultima_asistencia else 30
            motivo.append(f"No asistió al gimnasio en más de {dias} días")

        # Agregamos al listado si hay algún motivo
        if motivo:
            cliente.motivo_inactividad = " y ".join(motivo)
            clientes_inactivos.append(cliente)

    return render(request, 'clientes/inactivos.html', {
        'clientes_inactivos': clientes_inactivos
    })


#  listará los QR DE LOS CLIENTES
from django.shortcuts import render
from .models import Cliente
import qrcode
import base64
from io import BytesIO

def listar_qr_clientes(request):
    clientes = Cliente.objects.all()  # Obtener todos los clientes

    # Generar los datos del QR y la imagen base64 para cada cliente
    qr_codes = []
    for cliente in clientes:
        qr_data = f"ID:{cliente.id}\nNombre:{cliente.nombre}\nApellido:{cliente.apellido}\nCelular:{cliente.numero_celular}"

        # Generar el QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Crear la imagen del QR
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Convertir a base64
        qr_code_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

        # Almacenar el QR y el cliente
        qr_codes.append({'cliente': cliente, 'qr_code_url': qr_code_url})

    return render(request, 'clientes/listar_qr.html', {'qr_codes': qr_codes})






@user_passes_test(lambda u: u.is_staff)
def crear_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_clientes')
    else:
        form = ClienteForm()
    return render(request, 'clientes/crear_cliente.html', {'form': form})


from django.shortcuts import get_object_or_404

@login_required
def eliminar_cliente(request, cliente_id):
    """
    Permite al administrador eliminar un cliente.
    """
    if not request.user.is_staff:
        return redirect('home')

    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'POST':
        cliente.user.delete()  # Eliminar el usuario asociado
        cliente.delete()  # Eliminar el cliente
        return redirect('listar_clientes')

    return render(request, 'clientes/eliminar_cliente.html', {'cliente': cliente})



# /////////////////////////
# /////////////////////////
#  ASISTENCIA
# ////////////////////////
# //////////////////////



from django.db.models import Count
from datetime import date
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator  # Importamos Paginator
import logging
from .models import Asistencia
from clientes.models import Cliente

logger = logging.getLogger(__name__)

@login_required
def listar_asistencias(request):
    clientes = Cliente.objects.all()
    hoy = date.today()  # Fecha actual
    page_number = request.GET.get('page', 1)  # Número de página desde la URL

    if request.user.is_staff:
        asistencias = Asistencia.objects.all().order_by('-fecha')
        asistencia_hoy = None  # Los administradores no tienen asistencia propia
    else:
        try:
            cliente_actual = request.user.cliente
        except Cliente.DoesNotExist:
            logger.error(f"Cliente no encontrado para el usuario: {request.user.username}")
            return redirect('error_page')

        asistencias = Asistencia.objects.filter(cliente=cliente_actual).order_by('-fecha')
        asistencia_hoy = Asistencia.objects.filter(cliente=cliente_actual, fecha=hoy).first()

    # 🔹 Aplicar paginación (20 asistencias por página)
    paginator = Paginator(asistencias, 500)
    asistencias_paginadas = paginator.get_page(page_number)

    # 🔹 Agrupar asistencias por mes y día
    asistencias_por_mes = {}
    for asistencia in asistencias_paginadas:
        mes_anio = asistencia.fecha.strftime('%Y-%m')
        dia = asistencia.fecha.strftime('%d %B %Y')

        if mes_anio not in asistencias_por_mes:
            asistencias_por_mes[mes_anio] = {}

        if dia not in asistencias_por_mes[mes_anio]:
            asistencias_por_mes[mes_anio][dia] = []

        asistencias_por_mes[mes_anio][dia].append(asistencia)

    # 🔹 Resumen de asistencias mensuales
    if request.user.is_staff:
        asistencias_mensuales = Asistencia.objects.filter(presente=True).values(
            'cliente__nombre', 'cliente__apellido', 'fecha__month', 'fecha__year'
        ).annotate(total_asistencias=Count('id'))
    else:
        asistencias_mensuales = Asistencia.objects.filter(
            cliente=cliente_actual, presente=True
        ).values('cliente__nombre', 'cliente__apellido', 'fecha__month', 'fecha__year').annotate(total_asistencias=Count('id'))

    return render(request, 'clientes/listar_asistencias.html', {
        'asistencias_por_mes': asistencias_por_mes,
        'asistencias_mensuales': asistencias_mensuales,
        'asistencia_hoy': asistencia_hoy,
        'hoy': hoy,
        'asistencias_paginadas': asistencias_paginadas
    })




from django.shortcuts import render, redirect
from .forms import AsistenciaForm
from django.contrib.auth.decorators import login_required

@login_required
def crear_asistencia(request):
    if request.method == 'POST':
        form = AsistenciaForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('listar_asistencias')
    else:
        form = AsistenciaForm(user=request.user)
    return render(request, 'clientes/crear_asistencia.html', {'form': form})

def is_admin(user):
    return user.is_staff

@login_required
def editar_asistencia(request, id):
    asistencia = Asistencia.objects.get(id=id)
    if request.user.is_staff or asistencia.cliente.user == request.user:
        form = AsistenciaForm(request.POST or None, instance=asistencia, user=request.user)
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect('listar_asistencias')
    else:
        return redirect('error_page')  # Redirigir o mostrar un mensaje si el usuario no está autorizado
    return render(request, 'clientes/editar_asistencia.html', {'form': form})

@receiver(post_save, sender=Asistencia)
def actualizar_asistencia_mensual(sender, instance, **kwargs):
    mes_actual = instance.fecha.month
    anio_actual = instance.fecha.year

    # Contar las asistencias del cliente en el mes actual
    total_asistencias = Asistencia.objects.filter(
        cliente=instance.cliente,
        presente=True,
        fecha__year=anio_actual,
        fecha__month=mes_actual
    ).count()

    # Actualizar todas las instancias del mes actual con el nuevo total
    Asistencia.objects.filter(
        cliente=instance.cliente,
        fecha__year=anio_actual,
        fecha__month=mes_actual
    ).update(asistencia_mensual=total_asistencias)

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import user_passes_test

@login_required
@user_passes_test(lambda u: u.is_staff)  # Solo administradores pueden eliminar
def eliminar_asistencia(request, asistencia_id):
    asistencia = get_object_or_404(Asistencia, id=asistencia_id)
    asistencia.delete()
    return redirect('listar_asistencias')  # Redirige a la lista de asistencias



from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, get_object_or_404
from .models import Cliente, Pago
from datetime import date
from django.utils import timezone
from datetime import timedelta

# //////////////////////////////////////////////
# /////////////////////////////////////////////
#///////////////////////////////////         PAGOS       / /////////////////////////////////
# ///////////////////////////////////////////
# /////////////////////////////////////////////

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .models import Pago, Nota  # Nota debe estar correctamente definida

@login_required
def listar_pagos(request):
    # Obtenemos la consulta de búsqueda si existe
    query = request.GET.get('q')

    # Verificamos si el usuario es administrador
    if request.user.is_staff:  # Administradores ven todos los pagos
        if query:
            pagos = Pago.objects.filter(
                Q(fecha_pago__icontains=query) |
                Q(cliente__nombre__icontains=query) |
                Q(cliente__apellido__icontains=query) |
                Q(importe__icontains=query)
            ).order_by('-fecha_pago')
        else:
            pagos = Pago.objects.order_by('-fecha_pago')
    else:  # Usuarios normales ven solo sus pagos
        if query:
            pagos = Pago.objects.filter(
                Q(fecha_pago__icontains=query) |
                Q(importe__icontains=query),
                cliente__user=request.user  # Relación entre Cliente y User
            ).order_by('-fecha_pago')
        else:
            pagos = Pago.objects.filter(cliente__user=request.user).order_by('-fecha_pago')

    # Gestionamos las notas
    notas = Nota.objects.all()  # Verifica que el modelo Nota esté definido correctamente

    if request.method == "POST":
        if 'contenido' in request.POST:  # Agregar nueva nota
            contenido = request.POST['contenido']
            Nota.objects.create(contenido=contenido)
        elif 'nota_id' in request.POST:  # Eliminar una nota
            nota_id = request.POST['nota_id']
            Nota.objects.filter(id=nota_id).delete()

        return redirect('listar_pagos')

    return render(request, 'clientes/listar_pagos.html', {'pagos': pagos, 'notas': notas})



from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404

# Verifica que el usuario sea administrador
def admin_required(user):
    return user.is_staff

@user_passes_test(admin_required)
def eliminar_pago(request, id):
    pago = get_object_or_404(Pago, id=id)
    pago.delete()
    return redirect('listar_pagos')


def crear_pago(request):
    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_pagos')
    else:
        form = PagoForm()
    return render(request, 'clientes/crear_pago.html', {'form': form})

from django.contrib.auth.decorators import login_required, user_passes_test




from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def editar_pago(request, id):
    pago = get_object_or_404(Pago, id=id)

    if request.method == "POST":
        form = PagoForm(request.POST, instance=pago)
        if form.is_valid():
            form.save()
            messages.success(request, "Pago actualizado correctamente.")
            return redirect('listar_pagos')
    else:
        form = PagoForm(instance=pago)

    return render(request, 'clientes/editar_pago.html', {'form': form, 'pago': pago})







# ////////////////////////////////
# vista para calculo de recaudacion anual y mensual
# //////////////////////////////////////////////////////////////////////////////////////////////////
from django.shortcuts import render
from django.db.models import Sum
from .models import Pago
from django.contrib.auth.decorators import user_passes_test
import datetime

def is_admin(user):
    return user.is_staff

@user_passes_test(is_admin)
def recaudacion_view(request):
    import datetime
    hoy = datetime.date.today()
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    mes_actual = meses[hoy.month - 1]
    año_actual = hoy.year

    # Obtener recaudación total para el mes y el año
    recaudacion_mes = Pago.objects.filter(fecha_pago__year=hoy.year, fecha_pago__month=hoy.month).aggregate(Sum('importe'))['importe__sum'] or 0
    recaudacion_anual = Pago.objects.filter(fecha_pago__year=hoy.year).aggregate(Sum('importe'))['importe__sum'] or 0

    # Obtener pagos por cliente para el mes
    pagos_mes = Pago.objects.filter(fecha_pago__year=hoy.year, fecha_pago__month=hoy.month).order_by('fecha_pago')

    # Obtener pagos por cliente para el año
    pagos_anual = Pago.objects.filter(fecha_pago__year=hoy.year).order_by('fecha_pago')

    # Obtener la recaudación y pagos detallados por cada mes del año
    recaudacion_por_mes = {}
    for i in range(1, 13):
        mes_nombre = meses[i - 1]
        pagos_mes_actual = Pago.objects.filter(fecha_pago__year=hoy.year, fecha_pago__month=i)

        # Calcular el total de ingresos para ese mes
        total_mes = pagos_mes_actual.aggregate(Sum('importe'))['importe__sum'] or 0

        # Guardar en el diccionario el total y los pagos detallados
        recaudacion_por_mes[mes_nombre] = {
            'total': total_mes,
            'pagos': pagos_mes_actual  # Lista de pagos del mes con cliente e importe
        }

    context = {
        'recaudacion_mes': recaudacion_mes,
        'recaudacion_anual': recaudacion_anual,
        'pagos_mes': pagos_mes,
        'pagos_anual': pagos_anual,
        'mes_actual': mes_actual,
        'año_actual': año_actual,
        'recaudacion_por_mes': recaudacion_por_mes,  # Se enviará a la plantilla
    }

    return render(request, 'clientes/recaudacion.html', context)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def eliminar_nota(request, nota_id):
    if request.user.is_staff:
        try:
            nota = Nota.objects.get(id=nota_id)
            nota.delete()
            return JsonResponse({'success': True})
        except Nota.DoesNotExist:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})



# ///////////////////////////////////////////////////////7
# ////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////REFERIDO A  QR //////////////////
# ////////////////////////////////////////////////
# //////////////////////////////////////////////////////////




import qrcode
from io import BytesIO
import base64
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Cliente

# ✅ Generar QR para un cliente con datos formateados
def generar_qr(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    # 📌 Información que se guardará en el código QR
    qr_data = f"ID:{cliente.id}\nNombre:{cliente.nombre}\nApellido:{cliente.apellido}\nCelular:{cliente.numero_celular}"

    # ✅ Generar el QR con los datos formateados
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    # ✅ Crear imagen del QR
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # ✅ Convertir a base64 para mostrar en la plantilla
    qr_code_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

    return render(request, 'qr_cliente.html', {'cliente': cliente, 'qr_code_url': qr_code_url})


# ✅ Vista para escanear QR
def escanear_qr(request):
    return render(request, "escanear_qr.html")




from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.utils.timezone import now
from datetime import timedelta
from .models import Cliente, Asistencia, Pago

@csrf_exempt
def registrar_asistencia_qr(request):
    try:
        data = json.loads(request.body)
        cliente_id = data.get("cliente_id")

        if not cliente_id:
            return JsonResponse({"error": "No se recibió un ID de cliente válido"}, status=400)

        if "http" in cliente_id:
            cliente_id = cliente_id.rstrip("/").split("/")[-1]

        cliente_id = int(cliente_id)
        cliente = Cliente.objects.get(id=cliente_id)

        # Verificar si la membresía está vencida
        membresia_vencida = cliente.membresia_vencida()

        # Registrar asistencia
        asistencia, created = Asistencia.objects.get_or_create(
            cliente=cliente,
            fecha=now().date(),
            defaults={"presente": True}
        )

        if not created:
            asistencia.presente = True
            asistencia.save()

        # Determinar inactividad del usuario
        hoy = now().date()
        hace_dos_meses = hoy - timedelta(days=60)
        hace_un_mes = hoy - timedelta(days=30)

        ultima_asistencia = Asistencia.objects.filter(cliente=cliente).order_by('-fecha').first()
        ultimo_pago = Pago.objects.filter(cliente=cliente).order_by('-fecha_pago').first()

        motivo_inactividad = ""

        if not ultimo_pago or (ultimo_pago.fecha_pago < hace_dos_meses):
            motivo_inactividad = "No ha pagado la cuota en más de 60 días"

        if not ultima_asistencia or (ultima_asistencia.fecha < hace_un_mes):
            if motivo_inactividad:
                motivo_inactividad += " y no ha asistido en más de 30 días"
            else:
                motivo_inactividad = "No ha asistido en más de 30 días"

        return JsonResponse({
            "success": f"Asistencia registrada para {cliente.nombre}",
            "membresia_vencida": membresia_vencida,
            "motivo_inactividad": motivo_inactividad if motivo_inactividad else None
        })

    except Cliente.DoesNotExist:
        return JsonResponse({"error": "Cliente no encontrado"}, status=404)
    except ValueError:
        return JsonResponse({"error": "Formato de ID inválido"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Error en el formato de datos"}, status=400)

# escanea rapido la camara solo la0 isistencia

def escanear_qr_rapido(request):
    return render(request, "escaneo_rapido.html")



# ///////////////////////////////////////////////////////7
# ////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////CUOTA //////////////////
# ////////////////////////////////////////////////
# //////////////////////////////////////////////////////////




# para datos estadisticos
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from datetime import date


# Verifica si el usuario es admin
def es_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(es_admin)
def dashboard(request):
    total_clientes = Cliente.objects.count()
    presentes_hoy = Asistencia.objects.filter(fecha=date.today(), presente=True).count()
    ausentes_hoy = total_clientes - presentes_hoy
    total_recaudado = Pago.objects.aggregate(total=Sum('importe'))['total'] or 0

    # Cálculo del porcentaje de asistencia
    porcentaje_presentes = (presentes_hoy / total_clientes * 100) if total_clientes > 0 else 0

    context = {
        "total_clientes": total_clientes,
        "presentes_hoy": presentes_hoy,
        "ausentes_hoy": ausentes_hoy,
        "total_recaudado": total_recaudado,
        "porcentaje_presentes": round(porcentaje_presentes, 2)
    }

    return render(request, "dashboard.html", context)






def estado_cuota(request, cliente_id):
    try:
        # Recuperamos el cliente y los pagos asociados
        cliente = Cliente.objects.get(id=cliente_id)
        pagos = Pago.objects.filter(cliente=cliente).order_by('-fecha_pago')

        # Si existen pagos, calculamos la diferencia de días
        if pagos.exists():
            fecha_fin_pago = pagos[0].fecha_fin
            today_date = timezone.now().date()

            # Calculamos los días transcurridos desde la fecha de fin
            dias_transcurridos = (today_date - fecha_fin_pago).days
        else:
            dias_transcurridos = None

        return render(request, 'clientes/estado_cuota.html', {
            'cliente': cliente,
            'pagos': pagos,
            'dias_transcurridos': dias_transcurridos,
            'today_date': timezone.now().date(),  # Pasamos la fecha actual al template
        })

    except Cliente.DoesNotExist:
        return render(request, 'clientes/cliente_no_encontrado.html')



# renderiza, los clientes al dia, vencidos y por vencer
from django.shortcuts import render
from datetime import date, timedelta
from .models import Pago

# renderiza, los clientes al dia, vencidos y por vencer



from datetime import date, timedelta
from django.db.models import Max

def vencimientos_pagos(request):
    hoy = date.today()
    proximos_7_dias = hoy + timedelta(days=7)

    # Último pago por cliente
    ultimos_pagos = (
        Pago.objects
        .values('cliente')
        .annotate(ultima_fecha=Max('fecha_fin'))
    )

    pagos_ids = [
        Pago.objects.filter(cliente=p['cliente'], fecha_fin=p['ultima_fecha']).first().id
        for p in ultimos_pagos
    ]

    pagos = Pago.objects.filter(id__in=pagos_ids)

    pagos_vencidos = pagos.filter(fecha_fin__lt=hoy)
    pagos_por_vencer = pagos.filter(fecha_fin__gte=hoy, fecha_fin__lte=proximos_7_dias)
    pagos_al_dia = pagos.filter(fecha_fin__gt=proximos_7_dias)

    context = {
        'pagos_vencidos': pagos_vencidos,
        'pagos_por_vencer': pagos_por_vencer,
        'pagos_al_dia': pagos_al_dia,
    }

    return render(request, 'clientes/vencimientos.html', context)



# pagos en line y comprvantes desde aquiiiiiiiiiiiiiiiiiii

from django.shortcuts import render, redirect
from .models import ComprobantePago, Cliente
from .forms import ComprobantePagoForm

def pago_cuota_enlinea(request):
    datos_bancarios = {
        "cbu": "NDentrenamiento.21",
        "cvu": "----------",
        "qr": "/media/qr_gym.png"
    }

    comprobantes = ComprobantePago.objects.filter(cliente=request.user).order_by('-fecha_subida')

    # Buscar el cliente asociado al usuario
    cliente = Cliente.objects.filter(user=request.user).first()

    if request.method == "POST":
        form = ComprobantePagoForm(request.POST, request.FILES)
        if form.is_valid():
            comprobante = form.save(commit=False)
            comprobante.cliente = request.user
            comprobante.save()
            return redirect('pago_cuota_enlinea')

    else:
        form = ComprobantePagoForm()

    return render(request, "pago_cuota_enlinea.html", {
        "datos_bancarios": datos_bancarios,
        "form": form,
        "comprobantes": comprobantes,
        "cliente": cliente  # Enviamos el cliente al template
    })



# para que el admin borre los comrpobantes de pagos


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
import os
from django.conf import settings
from .models import ComprobantePago

def es_admin(user):
    return user.is_superuser  # Solo los admins pueden borrar

@user_passes_test(es_admin)
def eliminar_comprobante(request, comprobante_id):
    comprobante = get_object_or_404(ComprobantePago, id=comprobante_id)

    # Elimina el archivo físico del servidor
    ruta_archivo = os.path.join(settings.MEDIA_ROOT, str(comprobante.archivo))
    if os.path.exists(ruta_archivo):
        os.remove(ruta_archivo)

    # Elimina el registro de la base de datos
    comprobante.delete()

    messages.success(request, "Comprobante eliminado correctamente.")
    return redirect('listar_comprobantes')  # Ajusta según tu URL de listado

# para listalos comprobantes de pagos de los clientes
from django.contrib.auth.decorators import login_required

@login_required
def listar_comprobantes(request):
    comprobantes = ComprobantePago.objects.all().order_by('cliente__last_name', 'cliente__first_name')
    return render(request, 'clientes/listar_comprobantes.html', {'comprobantes': comprobantes})




# ///////////////////////////////////////////////////////7
# ////////////////////////////////////////////////////////
# //////////////////////////////////////////////////////////RUTINAS//////////////////
# ////////////////////////////////////////////////
# //////////////////////////////////////////////////////////


from django.shortcuts import render, get_object_or_404

from django.shortcuts import render, redirect
from .models import Rutina, Cliente
from .forms import RutinaForm

# si la cuota esta vencida , template de error
def cuota_vencida(request):
    return render(request, 'cuota_vencida.html')


def crear_rutina(request):
    if request.method == "POST":
        form = RutinaForm(request.POST, request.FILES)
        if form.is_valid():
            rutina = form.save(commit=False)  # Guardamos la rutina, pero sin confirmarla en la BD
            rutina.save()  # Ahora la guardamos en la base de datos

            # Obtener los IDs de los clientes seleccionados en el formulario
            cliente_ids = request.POST.getlist("cliente_ids")

            # Asignar los clientes a la rutina
            clientes = User.objects.filter(cliente__id__in=cliente_ids)  # Buscar el User asociado al Cliente
            rutina.clientes.add(*clientes)  # Ahora asignamos correctamente los usuarios

            return redirect("listar_rutinas")  # Redirigir al listado de rutinas después de guardar
    else:
        form = RutinaForm()

    # Pasamos los clientes disponibles al template
    clientes = Cliente.objects.all()

    return render(request, "rutinas/crear_rutina.html", {"form_rutina": form, "clientes": clientes})




from django.shortcuts import render
from .models import Grupo, Cliente

@login_required
def listar_rutinas(request):
    grupos = Grupo.objects.prefetch_related("subgrupos__rutina_set").all()
    clientes = Cliente.objects.all()  # Obtener todos los clientes
    rutinas = Rutina.objects.all()

    return render(request, "rutinas/listar_rutinas.html", {"grupos": grupos, "clientes": clientes})




from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Rutina

# @login_required
# def mi_rutina(request):
#     if not hasattr(request.user, 'cliente') or request.user.cliente.membresia_vencida():
#         return redirect('cuota_vencida')

#     rutinas = Rutina.objects.filter(clientes=request.user).order_by('fecha_creacion')
#     return render(request, "rutinas/mi_rutina.html", {"rutinas": rutinas})


from collections import defaultdict
from django.utils import timezone

@login_required
def mi_rutina(request):
    if not hasattr(request.user, 'cliente') or request.user.cliente.membresia_vencida():
        return redirect('cuota_vencida')

    rutinas = Rutina.objects.filter(clientes=request.user).order_by('fecha_creacion')

    # Agrupar por año y mes
    rutinas_por_mes = defaultdict(list)
    for rutina in rutinas:
        key = rutina.fecha_creacion.strftime("%B %Y")  # Ej: "Abril 2025"
        rutinas_por_mes[key].append(rutina)

    return render(request, "rutinas/mi_rutina.html", {"rutinas_por_mes": dict(rutinas_por_mes)})

# eliminar rutina
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from .models import Rutina

@login_required
def eliminar_rutina(request, rutina_id):
    rutina = get_object_or_404(Rutina, id=rutina_id)
    rutina.delete()
    return redirect('listar_rutinas')  # Cambiá a la vista correcta donde estás mostrando las rutinas


from django.contrib.auth.models import User
from .models import Rutina
from .forms import RutinaForm

def editar_rutina(request, rutina_id):
    rutina = get_object_or_404(Rutina, id=rutina_id)

    if request.method == "POST":
        form = RutinaForm(request.POST, request.FILES, instance=rutina)
        if form.is_valid():
            form.save()
            return redirect("listar_rutinas")
    else:
        form = RutinaForm(instance=rutina)

    return render(request, "rutinas/editar_rutina.html", {"form": form, "rutina": rutina})

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Rutina, Cliente


def asignar_cliente_a_rutina(request, rutina_id):
    if request.method == "POST":
        rutina = get_object_or_404(Rutina, id=rutina_id)
        cliente_id = request.POST.get("cliente_id")
        cliente = get_object_or_404(Cliente, id=cliente_id)

        rutina.clientes.add(cliente.user)
        messages.success(request, f"Cliente {cliente.nombre} asignado a la rutina {rutina.nombre}.")

    return redirect("listar_rutinas")





# elimina todos los clientes

from django.shortcuts import get_object_or_404, redirect
from .models import Rutina

def eliminar_todos_clientes_de_rutina(request, rutina_id):
    # Obtener la rutina
    rutina = get_object_or_404(Rutina, id=rutina_id)

    # Eliminar todos los clientes asignados
    rutina.clientes.clear()

    # Redirigir a la página de listar rutinas
    return redirect('listar_rutinas')



from django.shortcuts import get_object_or_404, redirect
from .models import Rutina, Cliente

def eliminar_cliente_de_rutina(request, rutina_id, cliente_id):
    # Obtén la rutina y el cliente correspondiente
    rutina = get_object_or_404(Rutina, id=rutina_id)
    cliente = get_object_or_404(Cliente, id=cliente_id)

    # Obtén el usuario asociado al cliente
    user = cliente.user  # Este es el objeto User relacionado con Cliente

    # Elimina el usuario de la rutina
    rutina.clientes.remove(user)
    return redirect('listar_rutinas')  # Cambia 'nombre_de_la_vista' por la vista correcta


# elimina grupos de rutina
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Grupo, Subgrupo

@login_required
def eliminar_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, id=grupo_id)

    # Eliminar todas las relaciones de subgrupos y rutinas
    grupo.subgrupos.all().delete()  # Eliminar subgrupos
    grupo.rutina_set.all().delete()  # Eliminar rutinas asociadas

    # Finalmente eliminar el grupo
    grupo.delete()
    return redirect('listar_rutinas')  # Redirigir a la página de listado

# elimina subgrupo de rutinas
@login_required
def eliminar_subgrupo(request, subgrupo_id):
    subgrupo = get_object_or_404(Subgrupo, id=subgrupo_id)

    # Eliminar todas las rutinas asociadas al subgrupo
    subgrupo.rutina_set.all().delete()

    # Eliminar el subgrupo
    subgrupo.delete()
    return redirect('listar_rutinas')  # Redirigir a la página de listado



# //////////////////////////////nutricion////////////////////////



from django.shortcuts import render, redirect
from .models import PlanNutricional, Cliente
from .forms import PlanNutricionalForm

def crear_plan_nutricional(request):
    if request.method == "POST":
        form = PlanNutricionalForm(request.POST, request.FILES)
        if form.is_valid():
            plan_nutricional = form.save(commit=False)  # Guardamos el plan, pero sin confirmarlo en la BD
            plan_nutricional.save()  # Ahora lo guardamos en la base de datos

            # Obtener los IDs de los clientes seleccionados en el formulario
            cliente_ids = request.POST.getlist("cliente_ids")

            # Asignar los clientes al plan nutricional
            clientes = User.objects.filter(cliente__id__in=cliente_ids)  # Buscar el User asociado al Cliente
            plan_nutricional.clientes.add(*clientes)  # Ahora asignamos correctamente los usuarios

            return redirect("listar_planes_nutricionales")  # Redirigir al listado de planes nutricionales después de guardar
    else:
        form = PlanNutricionalForm()

    # Pasamos los clientes disponibles al template
    clientes = Cliente.objects.all()

    return render(request, "nutricion/crear_plan_nutricional.html", {"form_nutricion": form, "clientes": clientes})



from django.shortcuts import render
from .models import PlanNutricional, Cliente, Categoria

@login_required
def listar_planes_nutricionales(request):
    categorias = Categoria.objects.prefetch_related("subcategorias__plannutricional_set").all()

    clientes = Cliente.objects.all()  # Obtener todos los clientes
    planes = PlanNutricional.objects.all()

    return render(request, "nutricion/listar_planes_nutricionales.html",{"categorias": categorias, "clientes": clientes})

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import PlanNutricional

@login_required
def mi_plan_nutricional(request):
    if not hasattr(request.user, 'cliente') or request.user.cliente.membresia_vencida():
        return redirect('cuota_vencida')  # Redirigir si no tiene cliente o su cuota está vencida

    planes = PlanNutricional.objects.filter(clientes=request.user).order_by('-fecha_creacion')
    return render(request, "nutricion/mi_plan_nutricional.html", {"planes": planes})


from django.shortcuts import get_object_or_404, redirect
from .forms import PlanNutricionalForm
from .models import PlanNutricional

def editar_plan_nutricional(request, plan_nutricional_id):
    plan_nutricional = get_object_or_404(PlanNutricional, id=plan_nutricional_id)

    if request.method == "POST":
        form = PlanNutricionalForm(request.POST, request.FILES, instance=plan_nutricional)
        if form.is_valid():
            form.save()
            return redirect("listar_planes_nutricionales")
    else:
        form = PlanNutricionalForm(instance=plan_nutricional)

    return render(request, "nutricion/editar_plan_nutricional.html", {"form": form, "plan_nutricional": plan_nutricional})


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import PlanNutricional, Cliente

def asignar_cliente_a_plan_nutricional(request, plan_nutricional_id):
    if request.method == "POST":
        plan_nutricional = get_object_or_404(PlanNutricional, id=plan_nutricional_id)
        cliente_id = request.POST.get("cliente_id")
        cliente = get_object_or_404(Cliente, id=cliente_id)

        plan_nutricional.clientes.add(cliente.user)
        messages.success(request, f"Cliente {cliente.nombre} asignado al plan nutricional {plan_nutricional.nombre}.")

    return redirect("listar_planes_nutricionales")

from django.shortcuts import get_object_or_404, redirect
from .models import PlanNutricional

def eliminar_todos_clientes_de_plan_nutricional(request, plan_nutricional_id):
    plan_nutricional = get_object_or_404(PlanNutricional, id=plan_nutricional_id)
    plan_nutricional.clientes.clear()

    return redirect('listar_planes_nutricionales')

from django.shortcuts import get_object_or_404, redirect
from .models import PlanNutricional, Cliente

def eliminar_cliente_de_plan_nutricional(request, plan_nutricional_id, cliente_id):
    plan_nutricional = get_object_or_404(PlanNutricional, id=plan_nutricional_id)
    cliente = get_object_or_404(Cliente, id=cliente_id)

    # Elimina el usuario de la lista de clientes del plan nutricional
    plan_nutricional.clientes.remove(cliente.user)
    return redirect('listar_planes_nutricionales')


from django.shortcuts import get_object_or_404, redirect
from .models import PlanNutricional, Cliente

def eliminar_cliente_de_plan(request, plan_id, cliente_id):
    # Obtén el plan nutricional y el cliente correspondiente
    plan = get_object_or_404(PlanNutricional, id=plan_id)
    cliente = get_object_or_404(Cliente, id=cliente_id)

    # Obtén el usuario asociado al cliente
    user = cliente.user  # Este es el objeto User relacionado con Cliente

    # Elimina el usuario del plan nutricional
    plan.clientes.remove(user)
    return redirect('listar_planes_nutricionales')  # Asegúrate de tener esta vista en tus URLs



# elimina ctegorias
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Categoria, Subcategoria

@login_required
def eliminar_categoria(request, id):
    categoria = get_object_or_404(Categoria, id=id)

    # Eliminar todas las relaciones de subcategorías y planes nutricionales
    categoria.subcategoria_set.all().delete()  # Eliminar subcategorías asociadas
    categoria.plan_nutricional_set.all().delete()  # Si hay planes asociados a la categoría

    # Finalmente, eliminar la categoría
    categoria.delete()

    return redirect('listar_planes_nutricionales')  # Redirigir a la lista de planes

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Subcategoria  # Asegúrate de importar el modelo correcto

@login_required
def eliminar_subcategoria(request, subcategoria_id):
    subcategoria = get_object_or_404(Subcategoria, id=subcategoria_id)

    # Eliminar todos los planes nutricionales asociados a la subcategoría
    subcategoria.plannutricional_set.all().delete()

    # Eliminar la subcategoría
    subcategoria.delete()
    return redirect('listar_planes_nutricionales')  # Redirigir a la vista de planes




# superadmin sebas, pirueee@gmail.com,sebas2025


# superadmin sebas, pirueee@gmail.com,sebas2025