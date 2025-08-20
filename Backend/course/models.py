from django.db import models
from django.urls import reverse
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db.models.signals import pre_save, post_save, post_delete
from django.db.models import Q
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

# project import
from .utils import *
from core.models import ActivityLog

YEARS = (
    (1, "1"),
    (2, "2"),
    (3, "3"),
    (4, "4"),
    (4, "5"),
    (4, "6"),
)

# LEVEL_COURSE = "Level course"
BACHELOR_DEGREE = _("Bachelor")
MASTER_DEGREE = _("Master")

LEVEL = (
    # (LEVEL_COURSE, "Level course"),
    (BACHELOR_DEGREE, _("Bachelor Degree")),
    (MASTER_DEGREE, _("Master Degree")),
)

FIRST = _("First")
SECOND = _("Second")
THIRD = _("Third")

SEMESTER = (
    (FIRST, _("First")),
    (SECOND, _("Second")),
    (THIRD, _("Third")),
)

# Nuevas opciones para cursos profesionales
MODALITY_CHOICES = (
    ('presencial', _('Presencial')),
    ('e-learning', _('E-learning')),
    ('hibrido', _('Híbrido')),
    ('intensivo', _('Intensivo')),
)

CATEGORY_CHOICES = (
    ('desarrollo_profesional', _('Desarrollo Profesional y Liderazgo')),
    ('tecnologia', _('Tecnología e Innovación')),
    ('gestion_empresarial', _('Gestión Empresarial')),
    ('marketing_ventas', _('Marketing y Ventas')),
    ('recursos_humanos', _('Recursos Humanos')),
    ('finanzas', _('Finanzas y Contabilidad')),
    ('operaciones', _('Operaciones y Logística')),
    ('comunicacion', _('Comunicación y Relaciones Públicas')),
    ('salud_bienestar', _('Salud y Bienestar')),
    ('educacion', _('Educación y Capacitación')),
    ('otros', _('Otros')),
)

DURATION_UNIT_CHOICES = (
    ('horas', _('Horas')),
    ('dias', _('Días')),
    ('semanas', _('Semanas')),
    ('meses', _('Meses')),
)


class ProgramManager(models.Manager):
    def search(self, query=None):
        queryset = self.get_queryset()
        if query is not None:
            or_lookup = Q(title__icontains=query) | Q(summary__icontains=query)
            queryset = queryset.filter(
                or_lookup
            ).distinct()  # distinct() is often necessary with Q lookups
        return queryset


class Program(models.Model):
    title = models.CharField(max_length=150, unique=True)
    summary = models.TextField(null=True, blank=True)

    objects = ProgramManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("course:program_detail", kwargs={"pk": self.pk})


@receiver(post_save, sender=Program)
def log_save(sender, instance, created, **kwargs):
    verb = "created" if created else "updated"
    ActivityLog.objects.create(message=_(f"The program '{instance}' has been {verb}."))


@receiver(post_delete, sender=Program)
def log_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(message=_(f"The program '{instance}' has been deleted."))


class CourseManager(models.Manager):
    def search(self, query=None):
        queryset = self.get_queryset()
        if query is not None:
            or_lookup = (
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(code__icontains=query)
                | Q(slug__icontains=query)
            )
            queryset = queryset.filter(
                or_lookup
            ).distinct()  # distinct() is often necessary with Q lookups
        return queryset


class Course(models.Model):
    slug = models.SlugField(blank=True, unique=True)
    title = models.CharField(max_length=200, null=True)
    code = models.CharField(max_length=200, unique=True, null=True)
    credit = models.IntegerField(null=True, default=0)
    summary = models.TextField(max_length=200, blank=True, null=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    level = models.CharField(max_length=25, choices=LEVEL, null=True)
    year = models.IntegerField(choices=YEARS, default=0)
    semester = models.CharField(choices=SEMESTER, max_length=200)
    is_elective = models.BooleanField(default=False, blank=True, null=True)
    
    # Imagen del curso
    image = models.ImageField(
        upload_to="course_images/%Y/%m/%d/",
        blank=True,
        null=True,
        help_text=_("Imagen representativa del curso (recomendado: 800x600px)")
    )
    
    # Nuevos campos para cursos profesionales
    objectives = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Lista de objetivos específicos del curso")
    )
    target_audience = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Descripción del público objetivo")
    )
    duration = models.IntegerField(
        blank=True, 
        null=True,
        help_text=_("Duración del curso")
    )
    duration_unit = models.CharField(
        max_length=10,
        choices=DURATION_UNIT_CHOICES,
        default='horas',
        blank=True,
        null=True
    )
    modality = models.CharField(
        max_length=20,
        choices=MODALITY_CHOICES,
        default='presencial',
        blank=True,
        null=True
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='otros',
        blank=True,
        null=True
    )
    prerequisites = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Requisitos previos para tomar el curso")
    )
    methodology = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Metodología de enseñanza")
    )
    materials_included = models.TextField(
        blank=True, 
        null=True,
        help_text=_("Materiales incluidos en el curso")
    )
    certification = models.BooleanField(
        default=False,
        help_text=_("¿El curso incluye certificación?")
    )
    max_students = models.IntegerField(
        blank=True, 
        null=True,
        help_text=_("Número máximo de estudiantes")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("¿El curso está activo y disponible?")
    )

    objects = CourseManager()

    def __str__(self):
        return "{0} ({1})".format(self.title, self.code)

    def get_absolute_url(self):
        return reverse("course:course_single", kwargs={"slug": self.slug})

    def user_can_edit(self, user):
        """Return True if the given user can edit this course.

        A user can edit when:
        - Is superuser or staff admin
        - Is a lecturer allocated to this course
        """
        # Usuarios con privilegios globales
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return True

        # Lectores asignados al curso
        if getattr(user, "is_lecturer", False):
            try:
                return CourseAllocation.objects.filter(lecturer=user, courses=self).exists()
            except Exception:
                return False

        return False

    @property
    def is_current_semester(self):
        from core.models import Semester

        current_semester = Semester.objects.filter(is_current_semester=True).first()

        if current_semester and self.semester == current_semester.semester:
            return True
        else:
            return False

    @property
    def full_duration(self):
        """Retorna la duración completa con su unidad"""
        if self.duration and self.duration_unit:
            return f"{self.duration} {self.get_duration_unit_display()}"
        return ""

    @property
    def is_professional_course(self):
        """Determina si es un curso profesional basado en la categoría"""
        return self.category and self.category != 'otros'


def course_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)


pre_save.connect(course_pre_save_receiver, sender=Course)


@receiver(post_save, sender=Course)
def log_save(sender, instance, created, **kwargs):
    verb = "created" if created else "updated"
    ActivityLog.objects.create(message=_(f"The course '{instance}' has been {verb}."))


@receiver(post_delete, sender=Course)
def log_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(message=_(f"The course '{instance}' has been deleted."))


class CourseAllocation(models.Model):
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=_("allocated_lecturer"),
    )
    courses = models.ManyToManyField(Course, related_name=_("allocated_course"))
    session = models.ForeignKey(
        "core.Session", on_delete=models.CASCADE, blank=True, null=True
    )

    def __str__(self):
        return self.lecturer.get_full_name

    def get_absolute_url(self):
        return reverse("course:edit_allocated_course", kwargs={"pk": self.pk})


class Upload(models.Model):
    title = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to="course_files/",
        help_text="Valid Files: pdf, docx, doc, xls, xlsx, ppt, pptx, zip, rar, 7zip",
        validators=[
            FileExtensionValidator(
                [
                    "pdf",
                    "docx",
                    "doc",
                    "xls",
                    "xlsx",
                    "ppt",
                    "pptx",
                    "zip",
                    "rar",
                    "7zip",
                ]
            )
        ],
    )
    updated_date = models.DateTimeField(auto_now=True, auto_now_add=False, null=True)
    upload_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=True)

    def __str__(self):
        return str(self.file)[6:]

    def get_extension_short(self):
        ext = str(self.file).split(".")
        ext = ext[len(ext) - 1]

        if ext in ("doc", "docx"):
            return "word"
        elif ext == "pdf":
            return "pdf"
        elif ext in ("xls", "xlsx"):
            return "excel"
        elif ext in ("ppt", "pptx"):
            return "powerpoint"
        elif ext in ("zip", "rar", "7zip"):
            return "archive"

    def delete(self, *args, **kwargs):
        self.file.delete()
        super().delete(*args, **kwargs)


@receiver(post_save, sender=Upload)
def log_save(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            message=_(
                f"The file '{instance.title}' has been uploaded to the course '{instance.course}'."
            )
        )
    else:
        ActivityLog.objects.create(
            message=_(
                f"The file '{instance.title}' of the course '{instance.course}' has been updated."
            )
        )


@receiver(post_delete, sender=Upload)
def log_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        message=_(
            f"The file '{instance.title}' of the course '{instance.course}' has been deleted."
        )
    )


class UploadVideo(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    video = models.FileField(
        upload_to="course_videos/",
        help_text=_("Valid video formats: mp4, mkv, wmv, 3gp, f4v, avi, mp3"),
        validators=[
            FileExtensionValidator(["mp4", "mkv", "wmv", "3gp", "f4v", "avi", "mp3"])
        ],
    )
    summary = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True, null=True)

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse(
            "course:video_single_view", kwargs={"slug": self.course.slug, "video_slug": self.slug}
        )

    def delete(self, *args, **kwargs):
        self.video.delete()
        super().delete(*args, **kwargs)


def video_pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance)


pre_save.connect(video_pre_save_receiver, sender=UploadVideo)


@receiver(post_save, sender=UploadVideo)
def log_save(sender, instance, created, **kwargs):
    if created:
        ActivityLog.objects.create(
            message=_(
                f"The video '{instance.title}' has been uploaded to the course {instance.course}."
            )
        )
    else:
        ActivityLog.objects.create(
            message=_(
                f"The video '{instance.title}' of the course '{instance.course}' has been updated."
            )
        )


@receiver(post_delete, sender=UploadVideo)
def log_delete(sender, instance, **kwargs):
    ActivityLog.objects.create(
        message=_(
            f"The video '{instance.title}' of the course '{instance.course}' has been deleted."
        )
    )


class CourseOffer(models.Model):
    _("""NOTE: Only department head can offer semester courses""")

    dep_head = models.ForeignKey("accounts.DepartmentHead", on_delete=models.CASCADE)

    def __str__(self):
        return "{}".format(self.dep_head)

# Nuevos modelos para sistema de módulos
class Module(models.Model):
    """Modelo para módulos de cursos"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200, help_text=_("Título del módulo"))
    description = models.TextField(help_text=_("Descripción del módulo"))
    order = models.PositiveIntegerField(default=0, help_text=_("Orden del módulo en el curso"))
    image = models.ImageField(
        upload_to="module_images/%Y/%m/%d/",
        blank=True,
        null=True,
        help_text=_("Imagen de portada del módulo")
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ['course', 'order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def get_absolute_url(self):
        return reverse("course:module_detail", kwargs={"slug": self.course.slug, "module_id": self.id})

    @property
    def lessons_count(self):
        return self.lessons.count()

    @property
    def total_duration(self):
        return sum(lesson.duration_minutes for lesson in self.lessons.all() if lesson.duration_minutes)


class Lesson(models.Model):
    """Modelo para lecciones dentro de módulos"""
    LESSON_TYPES = (
        ('video', _('Video')),
        ('text', _('Texto')),
        ('quiz', _('Cuestionario')),
        ('activity', _('Actividad Práctica')),
        ('assignment', _('Tarea')),
    )

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200, help_text=_("Título de la lección"))
    description = models.TextField(blank=True, null=True, help_text=_("Descripción de la lección"))
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='text')
    order = models.PositiveIntegerField(default=0, help_text=_("Orden de la lección en el módulo"))
    duration_minutes = models.PositiveIntegerField(default=0, help_text=_("Duración estimada en minutos"))
    is_required = models.BooleanField(default=True, help_text=_("¿Es obligatoria esta lección?"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ['module', 'order']

    def __str__(self):
        return f"{self.module.title} - {self.title}"

    def get_absolute_url(self):
        return reverse("course:lesson_detail", kwargs={
            "slug": self.module.course.slug, 
            "module_id": self.module.id,
            "lesson_id": self.id
        })


class LessonContent(models.Model):
    """Modelo para contenido de lecciones"""
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='content')
    text_content = models.TextField(blank=True, null=True, help_text=_("Contenido de texto de la lección"))
    video_url = models.URLField(blank=True, null=True, help_text=_("URL del video (YouTube, Vimeo, etc.)"))
    video_file = models.FileField(
        upload_to="lesson_videos/%Y/%m/%d/",
        blank=True,
        null=True,
        help_text=_("Archivo de video local")
    )
    attachments = models.ManyToManyField('Upload', blank=True, help_text=_("Archivos adjuntos"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Contenido de {self.lesson.title}"

    @property
    def has_video(self):
        return bool(self.video_url or self.video_file)

    @property
    def has_text(self):
        return bool(self.text_content)


class Quiz(models.Model):
    """Modelo para cuestionarios"""
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200, help_text=_("Título del cuestionario"))
    description = models.TextField(blank=True, null=True, help_text=_("Descripción del cuestionario"))
    passing_score = models.PositiveIntegerField(default=70, help_text=_("Puntuación mínima para aprobar (%)"))
    time_limit_minutes = models.PositiveIntegerField(default=0, help_text=_("Límite de tiempo en minutos (0 = sin límite)"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cuestionario: {self.title}"

    @property
    def questions_count(self):
        return self.questions.count()


class QuizQuestion(models.Model):
    """Modelo para preguntas de cuestionarios"""
    QUESTION_TYPES = (
        ('multiple_choice', _('Opción Múltiple')),
        ('true_false', _('Verdadero/Falso')),
        ('short_answer', _('Respuesta Corta')),
        ('essay', _('Ensayo')),
    )

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField(help_text=_("Texto de la pregunta"))
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    order = models.PositiveIntegerField(default=0, help_text=_("Orden de la pregunta"))
    points = models.PositiveIntegerField(default=1, help_text=_("Puntos por pregunta"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Pregunta {self.order}: {self.question_text[:50]}..."


class QuizOption(models.Model):
    """Modelo para opciones de preguntas de opción múltiple"""
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=500, help_text=_("Texto de la opción"))
    is_correct = models.BooleanField(default=False, help_text=_("¿Es la respuesta correcta?"))
    order = models.PositiveIntegerField(default=0, help_text=_("Orden de la opción"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Opción {self.order}: {self.option_text[:30]}..."


class StudentProgress(models.Model):
    """Modelo para seguimiento del progreso del estudiante"""
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE, related_name='progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_progress')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_minutes = models.PositiveIntegerField(default=0, help_text=_("Tiempo dedicado en minutos"))
    notes = models.TextField(blank=True, null=True, help_text=_("Notas del estudiante"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'lesson']

    def __str__(self):
        return f"{self.student} - {self.lesson}"

    def save(self, *args, **kwargs):
        if self.is_completed and not self.completed_at:
            from django.utils import timezone
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)


class QuizAttempt(models.Model):
    """Modelo para intentos de cuestionarios"""
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.student} - {self.quiz} - {self.score}%"

    def save(self, *args, **kwargs):
        if self.score is not None:
            self.is_passed = self.score >= self.quiz.passing_score
        super().save(*args, **kwargs)


class QuizResponse(models.Model):
    """Modelo para respuestas de cuestionarios"""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='responses')
    selected_option = models.ForeignKey(QuizOption, on_delete=models.CASCADE, null=True, blank=True)
    text_response = models.TextField(blank=True, null=True, help_text=_("Respuesta de texto para preguntas abiertas"))
    is_correct = models.BooleanField(default=False)
    points_earned = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Respuesta de {self.attempt.student} - {self.question}"


class ActivitySubmission(models.Model):
    """Modelo para entregas de actividades prácticas"""
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE, related_name='activity_submissions')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='submissions')
    title = models.CharField(max_length=200, help_text=_("Título de la entrega"))
    description = models.TextField(blank=True, null=True, help_text=_("Descripción de la entrega"))
    file = models.FileField(
        upload_to="activity_submissions/%Y/%m/%d/",
        blank=True,
        null=True,
        help_text=_("Archivo de la entrega")
    )
    image = models.ImageField(
        upload_to="activity_submissions/%Y/%m/%d/",
        blank=True,
        null=True,
        help_text=_("Imagen de la entrega")
    )
    url = models.URLField(blank=True, null=True, help_text=_("URL de la entrega (si es online)"))
    is_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True, null=True, help_text=_("Comentarios del instructor"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'lesson']
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student} - {self.lesson} - {self.title}"

    def save(self, *args, **kwargs):
        if self.is_submitted and not self.submitted_at:
            from django.utils import timezone
            self.submitted_at = timezone.now()
        super().save(*args, **kwargs)


class LessonBlock(models.Model):
    """Modelo para bloques de contenido de lecciones"""
    BLOCK_TYPES = (
        ('text', _('Bloque de Texto')),
        ('video', _('Video')),
        ('image', _('Imagen')),
        ('quiz', _('Cuestionario')),
        ('file', _('Archivo/Documento')),
        ('presentation', _('Presentación')),
        ('code', _('Código')),
        ('audio', _('Audio')),
        ('embed', _('Contenido Embebido')),
        ('divider', _('Separador')),
    )

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='blocks')
    block_type = models.CharField(max_length=20, choices=BLOCK_TYPES, help_text=_("Tipo de bloque"))
    order = models.PositiveIntegerField(help_text=_("Orden del bloque en la lección"), default=0)
    title = models.CharField(max_length=200, blank=True, null=True, help_text=_("Título del bloque"))
    
    def save(self, *args, **kwargs):
        # Asignar orden secuencial automáticamente al crear
        if not self.id:
            max_order = LessonBlock.objects.filter(
                lesson=self.lesson,
                is_active=True
            ).aggregate(models.Max('order'))['order__max']
            self.order = (max_order or 0) + 1

        # Asegurar valores por defecto visuales
        if not self.height:
            self.height = 'auto'
        if not self.width:
            self.width = '100%'

        super().save(*args, **kwargs)
    
    # Contenido de texto/HTML
    text_content = models.TextField(blank=True, null=True, help_text=_("Contenido de texto (soporta HTML)"))
    
    # Contenido multimedia
    video_url = models.URLField(blank=True, null=True, help_text=_("URL del video (YouTube, Vimeo, etc.)"))
    video_file = models.FileField(
        upload_to="lesson_videos/%Y/%m/%d/",
        blank=True,
        null=True,
        help_text=_("Archivo de video local")
    )
    audio_file = models.FileField(
        upload_to="lesson_audios/%Y/%m/%d/",
        blank=True,
        null=True,
        help_text=_("Archivo de audio")
    )
    image = models.ImageField(
        upload_to="lesson_images/%Y/%m/%d/",
        blank=True,
        null=True,
        help_text=_("Imagen")
    )
    file = models.FileField(
        upload_to="lesson_files/%Y/%m/%d/",
        blank=True,
        null=True,
        help_text=_("Archivo/documento")
    )
    
    # URLs y contenido embebido
    embed_url = models.URLField(blank=True, null=True, help_text=_("URL para contenido embebido"))
    embed_code = models.TextField(blank=True, null=True, help_text=_("Código HTML para embeber"))
    
    # Configuración del bloque
    width = models.CharField(
        max_length=10,
        default='100%',
        help_text=_("Ancho del bloque (ej: 100%, 50%, 300px)")
    )
    height = models.CharField(
        max_length=10,
        default='auto',
        help_text=_("Alto del bloque (ej: auto, 300px)")
    )
    background_color = models.CharField(
        max_length=7,
        default="#ffffff",
        blank=True,
        null=True,
        help_text=_("Color de fondo del bloque")
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Indica si el bloque está activo")
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.lesson.title} - {self.get_block_type_display()} - {self.order}"

    @property
    def has_content(self):
        """Verifica si el bloque tiene algún tipo de contenido"""
        def _filled(value):
            if value is None:
                return False
            # Normalizar a string para detectar valores basura como "[]", "{}", "null"
            if isinstance(value, (str, bytes)):
                try:
                    text = value.decode() if isinstance(value, bytes) else value
                except Exception:
                    text = str(value)
                text = text.strip().strip('\u200b')  # quitar whitespace y zero-width
                return text not in ("", "[]", "{}", "null", "None", "undefined")
            return True

        return any([
            _filled(self.text_content),
            _filled(self.video_url) or bool(self.video_file),
            bool(self.audio_file),
            bool(self.image),
            bool(self.file),
            _filled(self.embed_url) or _filled(self.embed_code),
        ])


class QuizBlock(models.Model):
    """Modelo específico para bloques de cuestionario"""
    lesson_block = models.OneToOneField(LessonBlock, on_delete=models.CASCADE, related_name='quiz_block')
    title = models.CharField(max_length=200, help_text=_("Título del cuestionario"))
    description = models.TextField(blank=True, null=True, help_text=_("Descripción del cuestionario"))
    passing_score = models.PositiveIntegerField(default=70, help_text=_("Puntuación mínima para aprobar (%)"))
    time_limit_minutes = models.PositiveIntegerField(default=0, help_text=_("Límite de tiempo en minutos (0 = sin límite)"))
    attempts_allowed = models.PositiveIntegerField(default=1, help_text=_("Intentos permitidos"))
    show_results = models.BooleanField(default=True, help_text=_("¿Mostrar resultados al finalizar?"))
    randomize_questions = models.BooleanField(default=False, help_text=_("¿Aleatorizar preguntas?"))

    def __str__(self):
        return f"Quiz: {self.title}"

    @property
    def questions_count(self):
        return self.questions.count()


class QuizBlockQuestion(models.Model):
    """Modelo para preguntas de cuestionarios en bloques"""
    QUESTION_TYPES = (
        ('multiple_choice', _('Opción Múltiple')),
        ('true_false', _('Verdadero/Falso')),
        ('short_answer', _('Respuesta Corta')),
        ('essay', _('Ensayo')),
        ('matching', _('Relacionar')),
        ('fill_blank', _('Llenar Espacios')),
    )

    quiz_block = models.ForeignKey(QuizBlock, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField(help_text=_("Texto de la pregunta"))
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    explanation = models.TextField(blank=True, null=True, help_text=_("Explicación de la respuesta"))
    order = models.PositiveIntegerField(default=0, help_text=_("Orden de la pregunta"))
    points = models.PositiveIntegerField(default=1, help_text=_("Puntos por pregunta"))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Pregunta {self.order}: {self.question_text[:50]}..."


class QuizBlockOption(models.Model):
    """Modelo para opciones de preguntas de cuestionarios en bloques"""
    question = models.ForeignKey(QuizBlockQuestion, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=500, help_text=_("Texto de la opción"))
    is_correct = models.BooleanField(default=False, help_text=_("¿Es la respuesta correcta?"))
    order = models.PositiveIntegerField(default=0, help_text=_("Orden de la opción"))

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Opción {self.order}: {self.option_text[:30]}..."
