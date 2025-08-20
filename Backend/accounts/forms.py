from django import forms
from django.db import transaction
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
)
from django.contrib.auth.forms import PasswordResetForm
from django.utils.translation import gettext_lazy as _
from course.models import Program
from .models import User, Student, Parent, RELATION_SHIP, LEVEL, GENDERS, DepartmentHead

# Opciones de roles para el registro
USER_ROLES = (
    ('student', _('Estudiante')),
    ('lecturer', _('Profesor')),
    ('parent', _('Padre')),
    ('dep_head', _('Jefe de Departamento')),
)


class UnifiedUserRegistrationForm(UserCreationForm):
    """Formulario unificado para registro de usuarios con selección de rol"""
    
    # Campos básicos
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Nombre"),
        required=True,
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Apellido"),
        required=True,
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
            }
        ),
        label=_("Correo Electrónico"),
        required=True,
    )
    
    address = forms.CharField(
        max_length=60,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Dirección"),
        required=True,
    )
    
    phone = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Teléfono"),
        required=True,
    )
    
    gender = forms.ChoiceField(
        choices=GENDERS,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
        label=_("Género"),
        required=True,
    )
    
    # Campo para seleccionar el rol
    user_role = forms.ChoiceField(
        choices=USER_ROLES,
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "id": "id_user_role"
            }
        ),
        label=_("Rol de Usuario"),
        required=True,
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si hay un valor inicial para user_role, asegurar que se establezca
        if 'initial' in kwargs and 'user_role' in kwargs['initial']:
            self.fields['user_role'].initial = kwargs['initial']['user_role']
    
    # Campos específicos para estudiantes
    level = forms.ChoiceField(
        choices=LEVEL,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
        label=_("Nivel"),
        required=False,  # Solo requerido para estudiantes
    )
    
    program = forms.ModelChoiceField(
        queryset=Program.objects.all(),
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
        label=_("Programa"),
        required=False,  # Solo requerido para estudiantes y jefes de departamento
        empty_label=_("Selecciona un programa")
    )
    
    # Campo específico para padres
    relation_ship = forms.ChoiceField(
        choices=RELATION_SHIP,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
        label=_("Relación"),
        required=False,  # Solo requerido para padres
    )
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'address', 'phone', 
                 'gender', 'user_role', 'level', 'program', 'relation_ship', 'password1', 'password2')
    
    def clean(self):
        cleaned_data = super().clean()
        user_role = cleaned_data.get('user_role')
        level = cleaned_data.get('level')
        program = cleaned_data.get('program')
        relation_ship = cleaned_data.get('relation_ship')
        
        # Validaciones específicas por rol
        if user_role == 'student':
            if not level:
                self.add_error('level', _('El nivel es requerido para estudiantes.'))
            if not program:
                self.add_error('program', _('El programa es requerido para estudiantes.'))
                
        elif user_role == 'dep_head':
            if not program:
                self.add_error('program', _('El programa es requerido para jefes de departamento.'))
                
        elif user_role == 'parent':
            if not relation_ship:
                self.add_error('relation_ship', _('La relación es requerida para padres.'))
        
        return cleaned_data
    
    @transaction.atomic()
    def save(self, commit=True):
        # Llamar a super().save() primero para que maneje la contraseña correctamente
        user = super().save(commit=False)
        
        # Marcar como registro público para evitar que el signal sobrescriba username/password
        user._public_registration = True
        
        # Establecer campos adicionales
        user.first_name = self.cleaned_data.get("first_name")
        user.last_name = self.cleaned_data.get("last_name")
        user.email = self.cleaned_data.get("email")
        user.address = self.cleaned_data.get("address")
        user.phone = self.cleaned_data.get("phone")
        user.gender = self.cleaned_data.get("gender")
        
        user_role = self.cleaned_data.get("user_role")
        
        # Establecer el rol correspondiente
        if user_role == 'student':
            user.is_student = True
        elif user_role == 'lecturer':
            user.is_lecturer = True
        elif user_role == 'parent':
            user.is_parent = True
        elif user_role == 'dep_head':
            user.is_dep_head = True
        
        if commit:
            # Guardar el usuario (ya con la contraseña hasheada por UserCreationForm)
            user.save()
            
            # Crear registros relacionados según el rol
            if user_role == 'student':
                Student.objects.create(
                    student=user,
                    level=self.cleaned_data.get("level"),
                    program=self.cleaned_data.get("program")
                )
            elif user_role == 'parent':
                Parent.objects.create(
                    user=user,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    phone=user.phone,
                    email=user.email,
                    relation_ship=self.cleaned_data.get("relation_ship")
                )
            elif user_role == 'dep_head':
                DepartmentHead.objects.create(
                    user=user,
                    department=self.cleaned_data.get("program")
                )
        
        return user

class StaffAddForm(UserCreationForm):
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "id": "username_id"
            }
        ),
        label=_("Nombre de Usuario"),
        required=True,
    )

    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Nombre"),
        required=True,
    )

    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Apellido"),
        required=True,
    )

    address = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Dirección"),
        required=True,
    )

    phone = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Teléfono"),
        required=True,
    )

    email = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "email",
                "class": "form-control",
            }
        ),
        label=_("Correo Electrónico"),
        required=True,
    )

    password1 = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "password",
                "class": "form-control",
            }
        ),
        label=_("Contraseña"),
        required=True,
    )

    password2 = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "password",
                "class": "form-control",
            }
        ),
        label=_("Confirmar Contraseña"),
        required=True,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'address', 'phone', 'password1', 'password2')

    @transaction.atomic()
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_lecturer = True
        user.first_name = self.cleaned_data.get("first_name")
        user.last_name = self.cleaned_data.get("last_name")
        user.phone = self.cleaned_data.get("phone")
        user.address = self.cleaned_data.get("address")
        user.email = self.cleaned_data.get("email")

        if commit:
            user.save()

        return user


class StudentAddForm(UserCreationForm):
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={"type": "text", "class": "form-control", "id": "username_id"}
        ),
        label=_("Nombre de Usuario"),
        required=True,
    )
    address = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Dirección"),
        required=True,
    )

    phone = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Número de Teléfono"),
        required=True,
    )

    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Nombre"),
        required=True,
    )

    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Apellido"),
        required=True,
    )

    gender = forms.CharField(
        widget=forms.Select(
            choices=GENDERS,
            attrs={
                "class": "browser-default custom-select form-control",
            },
        ),
        label=_("Género"),
        required=True,
    )

    level = forms.CharField(
        widget=forms.Select(
            choices=LEVEL,
            attrs={
                "class": "browser-default custom-select form-control",
            },
        ),
        label=_("Nivel"),
        required=True,
    )

    program = forms.ModelChoiceField(
        queryset=Program.objects.all(),
        widget=forms.Select(
            attrs={"class": "browser-default custom-select form-control"}
        ),
        label=_("Programa"),
        required=True,
    )

    email = forms.EmailField(
        widget=forms.TextInput(
            attrs={
                "type": "email",
                "class": "form-control",
            }
        ),
        label=_("Correo Electrónico"),
        required=True,
    )

    password1 = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "password",
                "class": "form-control",
            }
        ),
        label=_("Contraseña"),
        required=True,
    )

    password2 = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "password",
                "class": "form-control",
            }
        ),
        label=_("Confirmar Contraseña"),
        required=True,
    )

    # def validate_email(self):
    #     email = self.cleaned_data['email']
    #     if User.objects.filter(email__iexact=email, is_active=True).exists():
    #         raise forms.ValidationError("Email has taken, try another email address. ")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'address', 'phone', 'gender', 'level', 'program', 'password1', 'password2')

    @transaction.atomic()
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_student = True
        user.first_name = self.cleaned_data.get("first_name")
        user.last_name = self.cleaned_data.get("last_name")
        user.gender = self.cleaned_data.get("gender")
        user.address = self.cleaned_data.get("address")
        user.phone = self.cleaned_data.get("phone")
        user.email = self.cleaned_data.get("email")

        if commit:
            user.save()
            Student.objects.create(
                student=user,
                level=self.cleaned_data.get("level"),
                program=self.cleaned_data.get("program"),
            )

        return user


class ProfileUpdateForm(UserChangeForm):
    email = forms.EmailField(
        widget=forms.TextInput(
            attrs={
                "type": "email",
                "class": "form-control",
            }
        ),
        label=_("Correo Electrónico"),
    )

    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Nombre"),
    )

    last_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Apellido"),
    )

    gender = forms.CharField(
        widget=forms.Select(
            choices=GENDERS,
            attrs={
                "class": "browser-default custom-select form-control",
            },
        ),
    )

    phone = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Número de Teléfono"),
    )

    address = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Dirección / Ciudad"),
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "gender",
            "email",
            "phone",
            "address",
            "picture",
        ]


class ProgramUpdateForm(UserChangeForm):
    program = forms.ModelChoiceField(
        queryset=Program.objects.all(),
        widget=forms.Select(
            attrs={"class": "browser-default custom-select form-control"}
        ),
        label=_("Programa"),
    )

    class Meta:
        model = Student
        fields = ["program"]


class EmailValidationOnForgotPassword(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data["email"]
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            msg = "No hay ningún usuario registrado con la dirección de correo electrónico especificada."
            self.add_error("email", msg)
            return email


class ParentAddForm(UserCreationForm):
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Nombre de Usuario"),
    )
    address = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Dirección"),
    )

    phone = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Número de Teléfono"),
    )

    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Nombre"),
    )

    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
            }
        ),
        label=_("Apellido"),
    )

    email = forms.EmailField(
        widget=forms.TextInput(
            attrs={
                "type": "email",
                "class": "form-control",
            }
        ),
        label=_("Correo Electrónico"),
    )

    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        widget=forms.Select(
            attrs={"class": "browser-default custom-select form-control"}
        ),
        label=_("Estudiante"),
    )

    relation_ship = forms.CharField(
        widget=forms.Select(
            choices=RELATION_SHIP,
            attrs={
                "class": "browser-default custom-select form-control",
            },
        ),
    )

    password1 = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "password",
                "class": "form-control",
            }
        ),
        label=_("Contraseña"),
    )

    password2 = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "password",
                "class": "form-control",
            }
        ),
        label=_("Confirmar Contraseña"),
    )

    # def validate_email(self):
    #     email = self.cleaned_data['email']
    #     if User.objects.filter(email__iexact=email, is_active=True).exists():
    #         raise forms.ValidationError("Email has taken, try another email address. ")

    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic()
    def save(self):
        user = super().save(commit=False)
        user.is_parent = True
        user.first_name = self.cleaned_data.get("first_name")
        user.last_name = self.cleaned_data.get("last_name")
        user.address = self.cleaned_data.get("address")
        user.phone = self.cleaned_data.get("phone")
        user.email = self.cleaned_data.get("email")
        user.save()
        parent = Parent.objects.create(
            user=user,
            student=self.cleaned_data.get("student"),
            relation_ship=self.cleaned_data.get("relation_ship"),
        )
        parent.save()
        return user

class StudentEditForm(UserChangeForm):
    """Formulario completo para editar estudiantes con todos los campos"""
    
    # Campos del modelo User
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "placeholder": "Ingresa el nombre"
            }
        ),
        label=_("Nombre"),
        required=True,
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "placeholder": "Ingresa el apellido"
            }
        ),
        label=_("Apellido"),
        required=True,
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "ejemplo@email.com"
            }
        ),
        label=_("Correo Electrónico"),
        required=True,
    )
    
    phone = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "placeholder": "Número de teléfono"
            }
        ),
        label=_("Teléfono"),
        required=True,
    )
    
    address = forms.CharField(
        max_length=60,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "placeholder": "Dirección completa"
            }
        ),
        label=_("Dirección"),
        required=True,
    )
    
    gender = forms.ChoiceField(
        choices=GENDERS,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
        label=_("Género"),
        required=True,
    )
    
    picture = forms.ImageField(
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": "image/*"
            }
        ),
        label=_("Foto de Perfil"),
        required=False,
    )
    
    # Campos del modelo Student
    level = forms.ChoiceField(
        choices=LEVEL,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
        label=_("Nivel Académico"),
        required=True,
    )
    
    program = forms.ModelChoiceField(
        queryset=Program.objects.all(),
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
        label=_("Programa"),
        required=True,
        empty_label=_("Selecciona un programa")
    )
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'address', 
            'gender', 'picture', 'level', 'program'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Si es una instancia existente, obtener los datos del estudiante
            try:
                student = Student.objects.get(student=self.instance)
                self.fields['level'].initial = student.level
                self.fields['program'].initial = student.program
            except Student.DoesNotExist:
                pass
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Actualizar o crear el objeto Student
            student, created = Student.objects.get_or_create(student=user)
            student.level = self.cleaned_data.get('level')
            student.program = self.cleaned_data.get('program')
            student.save()
        return user


class LecturerEditForm(UserChangeForm):
    """Formulario completo para editar profesores con todos los campos"""
    
    # Campos del modelo User
    username = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "placeholder": "Nombre de usuario"
            }
        ),
        label=_("Nombre de Usuario"),
        required=True,
    )
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "placeholder": "Ingresa el nombre"
            }
        ),
        label=_("Nombre"),
        required=True,
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "placeholder": "Ingresa el apellido"
            }
        ),
        label=_("Apellido"),
        required=True,
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "ejemplo@email.com"
            }
        ),
        label=_("Correo Electrónico"),
        required=True,
    )
    
    phone = forms.CharField(
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "placeholder": "Número de teléfono"
            }
        ),
        label=_("Teléfono"),
        required=True,
    )
    
    address = forms.CharField(
        max_length=60,
        widget=forms.TextInput(
            attrs={
                "type": "text",
                "class": "form-control",
                "placeholder": "Dirección completa"
            }
        ),
        label=_("Dirección"),
        required=True,
    )
    
    gender = forms.ChoiceField(
        choices=GENDERS,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
        label=_("Género"),
        required=True,
    )
    
    picture = forms.ImageField(
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": "image/*"
            }
        ),
        label=_("Foto de Perfil"),
        required=False,
    )
    
    is_active = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
        label=_("Usuario Activo"),
        required=False,
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone', 
            'address', 'gender', 'picture', 'is_active'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer el campo username de solo lectura para evitar conflictos
        if self.instance and self.instance.pk:
            self.fields['username'].widget.attrs['readonly'] = True
            self.fields['username'].widget.attrs['class'] = 'form-control bg-light'
    
    def clean_username(self):
        """Mantener el username original si es una edición"""
        username = self.cleaned_data.get('username')
        if self.instance and self.instance.pk:
            return self.instance.username
        return username
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user
