from django import forms
from .models import Cliente, Asistencia, Pago

from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Requerido. Introduce un correo válido.")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'numero_celular', 'edad', 'fecha_nacimiento', 'enfermedades', 'alergias', 'imagen_perfil']

class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = ['cliente', 'fecha', 'presente']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(AsistenciaForm, self).__init__(*args, **kwargs)
        if user and not user.is_staff:
            self.fields['cliente'].queryset = Cliente.objects.filter(user=user)

from django.core.exceptions import ValidationError

class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['cliente', 'importe', 'fecha_inicio','fecha_fin', 'fecha_pago']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
            'fecha_pago': forms.DateInput(attrs={'type': 'date'}),
        }


    def clean_importe(self):
        importe = self.cleaned_data.get('importe')
        if importe <= 0:
            raise ValidationError('El importe debe ser un valor positivo.')
        return importe

    def clean_fecha_pago(self):
        fecha_inicio = self.cleaned_data.get('fecha_inicio')
        fecha_pago = self.cleaned_data.get('fecha_pago')
        if fecha_pago < fecha_inicio:
            raise ValidationError('La fecha de pago no puede ser anterior a la fecha de inicio.')
        return fecha_pago

# ///////////////////////////RUTINAS////////////////////

from django import forms
from .models import Rutina, Grupo, Subgrupo

class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ['nombre']

class SubgrupoForm(forms.ModelForm):
    class Meta:
        model = Subgrupo
        fields = ['nombre', 'grupo']

class RutinaForm(forms.ModelForm):
    class Meta:
        model = Rutina
        fields = ['nombre', 'descripcion', 'imagen', 'grupo', 'subgrupo', 'video_url']
        widgets = {
            'descripcion': forms.Textarea(attrs={'cols': 40, 'rows': 5}),
        }

    grupo_nuevo = forms.CharField(max_length=100, required=False, label="Nuevo Grupo")
    subgrupo_nuevo = forms.CharField(max_length=100, required=False, label="Nuevo Subgrupo")

    def save(self, commit=True):
        grupo = self.cleaned_data.get('grupo')
        subgrupo = self.cleaned_data.get('subgrupo')
        grupo_nuevo = self.cleaned_data.get('grupo_nuevo')
        subgrupo_nuevo = self.cleaned_data.get('subgrupo_nuevo')

        if grupo_nuevo:
            grupo, created = Grupo.objects.get_or_create(nombre=grupo_nuevo)
        if subgrupo_nuevo:
            subgrupo, created = Subgrupo.objects.get_or_create(nombre=subgrupo_nuevo, grupo=grupo)

        rutina = super().save(commit=False)
        rutina.grupo = grupo
        rutina.subgrupo = subgrupo

        if commit:
            rutina.save()
        return rutina



# formulario para subir comprobantez

from django import forms
from .models import ComprobantePago

class ComprobantePagoForm(forms.ModelForm):
    class Meta:
        model = ComprobantePago
        fields = ['archivo']

# ////////////////////////////////////nutricion grupos

from django import forms
from .models import PlanNutricional, Categoria, Subcategoria

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']

class SubcategoriaForm(forms.ModelForm):
    class Meta:
        model = Subcategoria
        fields = ['nombre', 'categoria']

class PlanNutricionalForm(forms.ModelForm):
    class Meta:
        model = PlanNutricional
        fields = ['nombre', 'descripcion', 'imagen', 'categoria', 'subcategoria', 'documento', 'video_url']
        widgets = {
            'descripcion': forms.Textarea(attrs={'cols': 40, 'rows': 5}),
        }

    categoria_nueva = forms.CharField(max_length=100, required=False, label="Nueva Categoría")
    subcategoria_nueva = forms.CharField(max_length=100, required=False, label="Nueva Subcategoría")

    def save(self, commit=True):
        categoria = self.cleaned_data.get('categoria')
        subcategoria = self.cleaned_data.get('subcategoria')
        categoria_nueva = self.cleaned_data.get('categoria_nueva')
        subcategoria_nueva = self.cleaned_data.get('subcategoria_nueva')

        if categoria_nueva:
            categoria, created = Categoria.objects.get_or_create(nombre=categoria_nueva)
        if subcategoria_nueva:
            subcategoria, created = Subcategoria.objects.get_or_create(nombre=subcategoria_nueva, categoria=categoria)

        plan_nutricional = super().save(commit=False)
        plan_nutricional.categoria = categoria
        plan_nutricional.subcategoria = subcategoria

        if commit:
            plan_nutricional.save()
        return plan_nutricional


