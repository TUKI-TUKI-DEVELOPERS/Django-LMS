from django import forms
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from .models import (
    Program, Course, CourseAllocation, Upload, UploadVideo, Module, Lesson, 
    LessonContent, Quiz, QuizQuestion, QuizOption, LessonBlock, QuizBlock, 
    QuizBlockQuestion, QuizBlockOption
)


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["summary"].widget.attrs.update({"class": "form-control"})
        self.fields["title"].label = _("Título")
        self.fields["summary"].label = _("Resumen")


class CourseAddForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Campos básicos del curso
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["code"].widget.attrs.update({"class": "form-control"})
        self.fields["credit"].widget.attrs.update({"class": "form-control"})
        self.fields["summary"].widget.attrs.update({"class": "form-control"})
        self.fields["program"].widget.attrs.update({"class": "form-control"})
        self.fields["level"].widget.attrs.update({"class": "form-control"})
        self.fields["year"].widget.attrs.update({"class": "form-control"})
        self.fields["semester"].widget.attrs.update({"class": "form-control"})
        
        # Campo de imagen
        self.fields["image"].widget.attrs.update({
            "class": "form-control",
            "accept": "image/*"
        })
        
        # Nuevos campos profesionales
        self.fields["objectives"].widget.attrs.update({"class": "form-control", "rows": "4"})
        self.fields["target_audience"].widget.attrs.update({"class": "form-control", "rows": "3"})
        self.fields["duration"].widget.attrs.update({"class": "form-control"})
        self.fields["duration_unit"].widget.attrs.update({"class": "form-control"})
        self.fields["modality"].widget.attrs.update({"class": "form-control"})
        self.fields["category"].widget.attrs.update({"class": "form-control"})
        self.fields["prerequisites"].widget.attrs.update({"class": "form-control", "rows": "3"})
        self.fields["methodology"].widget.attrs.update({"class": "form-control", "rows": "3"})
        self.fields["materials_included"].widget.attrs.update({"class": "form-control", "rows": "3"})
        self.fields["max_students"].widget.attrs.update({"class": "form-control"})
        
        # Campos booleanos
        self.fields["is_elective"].widget.attrs.update({"class": "form-check-input"})
        self.fields["certification"].widget.attrs.update({"class": "form-check-input"})
        self.fields["is_active"].widget.attrs.update({"class": "form-check-input"})
        
        # Traducir etiquetas básicas
        self.fields["title"].label = _("Título del Curso")
        self.fields["code"].label = _("Código del Curso")
        self.fields["credit"].label = _("Créditos")
        self.fields["summary"].label = _("Resumen del Curso")
        self.fields["program"].label = _("Programa")
        self.fields["level"].label = _("Nivel")
        self.fields["year"].label = _("Año")
        self.fields["semester"].label = _("Semestre")
        self.fields["is_elective"].label = _("¿Es Curso Electivo?")
        self.fields["image"].label = _("Imagen del Curso")
        
        # Traducir etiquetas de campos profesionales
        self.fields["objectives"].label = _("Objetivos del Curso")
        self.fields["target_audience"].label = _("Público Objetivo")
        self.fields["duration"].label = _("Duración")
        self.fields["duration_unit"].label = _("Unidad de Duración")
        self.fields["modality"].label = _("Modalidad")
        self.fields["category"].label = _("Categoría")
        self.fields["prerequisites"].label = _("Prerrequisitos")
        self.fields["methodology"].label = _("Metodología")
        self.fields["materials_included"].label = _("Materiales Incluidos")
        self.fields["certification"].label = _("¿Incluye Certificación?")
        self.fields["max_students"].label = _("Máximo de Estudiantes")
        self.fields["is_active"].label = _("¿Curso Activo?")


class CourseAllocationForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all().order_by("level"),
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "browser-default checkbox"}
        ),
        required=True,
        label=_("Cursos"),
    )
    lecturer = forms.ModelChoiceField(
        queryset=User.objects.filter(is_lecturer=True),
        widget=forms.Select(attrs={"class": "browser-default custom-select"}),
        label=_("Profesor"),
    )

    class Meta:
        model = CourseAllocation
        fields = ["lecturer", "courses"]

    def __init__(self, *args, **kwargs):
        # Permitir pasar el usuario desde la vista sin romper la firma del formulario
        self.request_user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["lecturer"].widget.attrs.update({"class": "form-control"})


class EditCourseAllocationForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all().order_by("level"),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label=_("Cursos"),
    )
    lecturer = forms.ModelChoiceField(
        queryset=User.objects.filter(is_lecturer=True),
        widget=forms.Select(attrs={"class": "browser-default custom-select"}),
        label=_("Profesor"),
    )

    class Meta:
        model = CourseAllocation
        fields = ["lecturer", "courses"]

    def __init__(self, *args, **kwargs):
        # Permitir pasar el usuario desde la vista sin romper la firma del formulario
        self.request_user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["lecturer"].widget.attrs.update({"class": "form-control"})


class UploadFormFile(forms.ModelForm):
    class Meta:
        model = Upload
        fields = (
            "title",
            "file",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["file"].widget.attrs.update({"class": "form-control"})


class UploadFormVideo(forms.ModelForm):
    class Meta:
        model = UploadVideo
        fields = (
            "title",
            "video",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["video"].widget.attrs.update({"class": "form-control"})


# Formularios para el sistema de módulos
class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'description', 'image', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["description"].widget.attrs.update({"class": "form-control", "rows": "4"})
        self.fields["image"].widget.attrs.update({
            "class": "form-control",
            "accept": "image/*"
        })
        self.fields["is_active"].widget.attrs.update({"class": "form-check-input"})
        
        # Traducir etiquetas
        self.fields["title"].label = _("Título del Módulo")
        self.fields["description"].label = _("Descripción")
        self.fields["image"].label = _("Imagen del Módulo")
        self.fields["is_active"].label = _("¿Módulo Activo?")


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'lesson_type', 'duration_minutes', 'is_required', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["description"].widget.attrs.update({"class": "form-control", "rows": "4"})
        self.fields["lesson_type"].widget.attrs.update({"class": "form-control"})
        self.fields["duration_minutes"].widget.attrs.update({"class": "form-control"})
        self.fields["is_required"].widget.attrs.update({"class": "form-check-input"})
        self.fields["is_active"].widget.attrs.update({"class": "form-check-input"})
        
        # Traducir etiquetas
        self.fields["title"].label = _("Título de la Lección")
        self.fields["description"].label = _("Descripción")
        self.fields["lesson_type"].label = _("Tipo de Lección")
        self.fields["duration_minutes"].label = _("Duración (minutos)")
        self.fields["is_required"].label = _("¿Es Requerida?")
        self.fields["is_active"].label = _("¿Lección Activa?")


class LessonContentForm(forms.ModelForm):
    class Meta:
        model = LessonContent
        fields = ['text_content', 'video_url', 'video_file', 'attachments']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["text_content"].widget.attrs.update({"class": "form-control", "rows": "8"})
        self.fields["video_url"].widget.attrs.update({"class": "form-control"})
        self.fields["video_file"].widget.attrs.update({"class": "form-control"})
        self.fields["attachments"].widget.attrs.update({"class": "form-control"})
        
        # Traducir etiquetas
        self.fields["text_content"].label = _("Contenido de Texto")
        self.fields["video_url"].label = _("URL del Video")
        self.fields["video_file"].label = _("Archivo de Video")
        self.fields["attachments"].label = _("Archivos Adjuntos")


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'passing_score', 'time_limit_minutes', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["description"].widget.attrs.update({"class": "form-control", "rows": "4"})
        self.fields["passing_score"].widget.attrs.update({"class": "form-control"})
        self.fields["time_limit_minutes"].widget.attrs.update({"class": "form-control"})
        self.fields["is_active"].widget.attrs.update({"class": "form-check-input"})
        
        # Traducir etiquetas
        self.fields["title"].label = _("Título del Quiz")
        self.fields["description"].label = _("Descripción")
        self.fields["passing_score"].label = _("Puntuación de Aprobación")
        self.fields["time_limit_minutes"].label = _("Límite de Tiempo (minutos)")
        self.fields["is_active"].label = _("¿Quiz Activo?")


class QuizQuestionForm(forms.ModelForm):
    class Meta:
        model = QuizQuestion
        fields = ['question_text', 'question_type', 'order', 'points', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["question_text"].widget.attrs.update({"class": "form-control", "rows": "3"})
        self.fields["question_type"].widget.attrs.update({"class": "form-control"})
        self.fields["order"].widget.attrs.update({"class": "form-control"})
        self.fields["points"].widget.attrs.update({"class": "form-control"})
        self.fields["is_active"].widget.attrs.update({"class": "form-check-input"})
        
        # Traducir etiquetas
        self.fields["question_text"].label = _("Pregunta")
        self.fields["question_type"].label = _("Tipo de Pregunta")
        self.fields["order"].label = _("Orden")
        self.fields["points"].label = _("Puntos")
        self.fields["is_active"].label = _("¿Pregunta Activa?")


class QuizOptionForm(forms.ModelForm):
    class Meta:
        model = QuizOption
        fields = ['option_text', 'is_correct', 'order']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["option_text"].widget.attrs.update({"class": "form-control"})
        self.fields["is_correct"].widget.attrs.update({"class": "form-check-input"})
        self.fields["order"].widget.attrs.update({"class": "form-control"})
        
        # Traducir etiquetas
        self.fields["option_text"].label = _("Texto de la Opción")
        self.fields["is_correct"].label = _("¿Es Correcta?")
        self.fields["order"].label = _("Orden")


# Formularios para el sistema de bloques de contenido
class LessonBlockForm(forms.ModelForm):
    class Meta:
        model = LessonBlock
        fields = [
            'block_type', 'title', 'text_content', 'video_url', 'video_file',
            'audio_file', 'image', 'file', 'embed_url', 'embed_code',
            'width', 'height', 'background_color', 'is_active'
        ]
        exclude = ['order']  # Excluir el campo order para que sea manejado automáticamente

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar widgets
        self.fields["block_type"].widget.attrs.update({"class": "form-control"})
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["text_content"].widget.attrs.update({
            "class": "form-control rich-editor",
            "rows": "8"
        })
        self.fields["video_url"].widget.attrs.update({"class": "form-control"})
        self.fields["video_file"].widget.attrs.update({"class": "form-control"})
        self.fields["audio_file"].widget.attrs.update({"class": "form-control"})
        self.fields["image"].widget.attrs.update({"class": "form-control"})
        self.fields["file"].widget.attrs.update({"class": "form-control"})
        self.fields["embed_url"].widget.attrs.update({"class": "form-control"})
        self.fields["embed_code"].widget.attrs.update({
            "class": "form-control",
            "rows": "4"
        })
        self.fields["width"].widget.attrs.update({"class": "form-control"})
        self.fields["height"].widget.attrs.update({"class": "form-control"})
        self.fields["background_color"].widget.attrs.update({
            "class": "form-control",
            "type": "color"
        })
        self.fields["is_active"].widget.attrs.update({"class": "form-check-input"})
        # Altura no obligatoria; usar 'auto' por defecto si viene vacía
        self.fields["height"].required = False
        self.fields["height"].initial = "auto"
        
        # Traducir etiquetas
        self.fields["block_type"].label = _("Tipo de Bloque")
        self.fields["title"].label = _("Título del Bloque")
        self.fields["text_content"].label = _("Contenido de Texto")
        self.fields["video_url"].label = _("URL del Video")
        self.fields["video_file"].label = _("Archivo de Video")
        self.fields["audio_file"].label = _("Archivo de Audio")
        self.fields["image"].label = _("Imagen")
        self.fields["file"].label = _("Archivo/Documento")
        self.fields["embed_url"].label = _("URL para Embeber")
        self.fields["embed_code"].label = _("Código HTML")
        self.fields["width"].label = _("Ancho")
        self.fields["height"].label = _("Alto")
        self.fields["background_color"].label = _("Color de Fondo")
        self.fields["is_active"].label = _("¿Bloque Activo?")


class QuizBlockForm(forms.ModelForm):
    class Meta:
        model = QuizBlock
        fields = [
            'title', 'description', 'passing_score', 'time_limit_minutes',
            'attempts_allowed', 'show_results', 'randomize_questions'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar widgets
        self.fields["title"].widget.attrs.update({"class": "form-control"})
        self.fields["description"].widget.attrs.update({
            "class": "form-control",
            "rows": "4"
        })
        self.fields["passing_score"].widget.attrs.update({"class": "form-control"})
        self.fields["time_limit_minutes"].widget.attrs.update({"class": "form-control"})
        self.fields["attempts_allowed"].widget.attrs.update({"class": "form-control"})
        self.fields["show_results"].widget.attrs.update({"class": "form-check-input"})
        self.fields["randomize_questions"].widget.attrs.update({"class": "form-check-input"})
        
        # Traducir etiquetas
        self.fields["title"].label = _("Título del Cuestionario")
        self.fields["description"].label = _("Descripción")
        self.fields["passing_score"].label = _("Puntuación de Aprobación (%)")
        self.fields["time_limit_minutes"].label = _("Límite de Tiempo (minutos)")
        self.fields["attempts_allowed"].label = _("Intentos Permitidos")
        self.fields["show_results"].label = _("¿Mostrar Resultados?")
        self.fields["randomize_questions"].label = _("¿Aleatorizar Preguntas?")


class QuizBlockQuestionForm(forms.ModelForm):
    class Meta:
        model = QuizBlockQuestion
        fields = ['question_text', 'question_type', 'explanation', 'order', 'points', 'is_active']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar widgets
        self.fields["question_text"].widget.attrs.update({
            "class": "form-control",
            "rows": "3"
        })
        self.fields["question_type"].widget.attrs.update({"class": "form-control"})
        self.fields["explanation"].widget.attrs.update({
            "class": "form-control",
            "rows": "3"
        })
        self.fields["order"].widget.attrs.update({"class": "form-control"})
        self.fields["points"].widget.attrs.update({"class": "form-control"})
        self.fields["is_active"].widget.attrs.update({"class": "form-check-input"})
        
        # Traducir etiquetas
        self.fields["question_text"].label = _("Pregunta")
        self.fields["question_type"].label = _("Tipo de Pregunta")
        self.fields["explanation"].label = _("Explicación")
        self.fields["order"].label = _("Orden")
        self.fields["points"].label = _("Puntos")
        self.fields["is_active"].label = _("¿Pregunta Activa?")


class QuizBlockOptionForm(forms.ModelForm):
    class Meta:
        model = QuizBlockOption
        fields = ['option_text', 'is_correct', 'order']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar widgets
        self.fields["option_text"].widget.attrs.update({"class": "form-control"})
        self.fields["is_correct"].widget.attrs.update({"class": "form-check-input"})
        self.fields["order"].widget.attrs.update({"class": "form-control"})
        
        # Traducir etiquetas
        self.fields["option_text"].label = _("Texto de la Opción")
        self.fields["is_correct"].label = _("¿Es Correcta?")
        self.fields["order"].label = _("Orden")
