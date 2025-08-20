from django.contrib import admin
from django.contrib.auth.models import Group

from .models import (
    Program, Course, CourseAllocation, Upload, 
    Module, Lesson, LessonContent, Quiz, QuizQuestion, 
    QuizOption, StudentProgress, QuizAttempt, QuizResponse, 
    ActivitySubmission, LessonBlock, QuizBlock, QuizBlockQuestion, 
    QuizBlockOption
)
from modeltranslation.admin import TranslationAdmin

class ProgramAdmin(TranslationAdmin):
    list_display = ['title', 'summary']
    search_fields = ['title', 'summary']
    list_filter = ['title']

class CourseAdmin(TranslationAdmin):
    list_display = ['title', 'code', 'program', 'level', 'year', 'semester', 'modality', 'category', 'is_active']
    list_filter = ['program', 'level', 'year', 'semester', 'modality', 'category', 'is_active', 'is_elective', 'certification']
    search_fields = ['title', 'code', 'summary', 'objectives']
    readonly_fields = ['slug']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'code', 'slug', 'summary', 'image', 'program')
        }),
        ('Información Académica', {
            'fields': ('level', 'year', 'semester', 'credit', 'is_elective')
        }),
        ('Información Profesional', {
            'fields': ('objectives', 'target_audience', 'duration', 'duration_unit', 'modality', 'category')
        }),
        ('Configuración Avanzada', {
            'fields': ('prerequisites', 'methodology', 'materials_included', 'max_students')
        }),
        ('Estado del Curso', {
            'fields': ('certification', 'is_active')
        }),
    )

class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'lessons_count', 'total_duration', 'is_active']
    list_filter = ['course', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'course__title']
    ordering = ['course', 'order']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('course', 'title', 'description', 'order', 'image')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
    )

class LessonContentInline(admin.StackedInline):
    model = LessonContent
    extra = 1
    fields = ('text_content', 'video_url', 'video_file', 'attachments')

class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'lesson_type', 'order', 'duration_minutes', 'is_required', 'is_active']
    list_filter = ['module__course', 'lesson_type', 'is_required', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'module__title']
    ordering = ['module', 'order']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('module', 'title', 'description', 'lesson_type', 'order')
        }),
        ('Configuración', {
            'fields': ('duration_minutes', 'is_required', 'is_active')
        }),
    )
    
    inlines = [LessonContentInline]

class QuizOptionInline(admin.TabularInline):
    model = QuizOption
    extra = 4
    fields = ('option_text', 'is_correct', 'order')

class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'quiz', 'question_type', 'order', 'points', 'is_active']
    list_filter = ['quiz', 'question_type', 'is_active']
    search_fields = ['question_text']
    ordering = ['quiz', 'order']
    
    fieldsets = (
        ('Pregunta', {
            'fields': ('quiz', 'question_text', 'question_type', 'order', 'points')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
    )
    
    inlines = [QuizOptionInline]

class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'questions_count', 'passing_score', 'time_limit_minutes', 'is_active']
    list_filter = ['lesson__module__course', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('lesson', 'title', 'description')
        }),
        ('Configuración', {
            'fields': ('passing_score', 'time_limit_minutes', 'is_active')
        }),
    )

class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'is_completed', 'time_spent_minutes', 'completed_at']
    list_filter = ['is_completed', 'lesson__module__course', 'completed_at']
    search_fields = ['student__student__first_name', 'student__student__last_name', 'lesson__title']
    readonly_fields = ['completed_at']
    
    fieldsets = (
        ('Progreso', {
            'fields': ('student', 'lesson', 'is_completed', 'time_spent_minutes')
        }),
        ('Información Adicional', {
            'fields': ('notes', 'completed_at')
        }),
    )

class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'quiz', 'score', 'is_passed', 'started_at', 'completed_at']
    list_filter = ['is_passed', 'quiz__lesson__module__course', 'started_at']
    search_fields = ['student__student__first_name', 'student__student__last_name', 'quiz__title']
    readonly_fields = ['started_at', 'completed_at']
    
    fieldsets = (
        ('Intento', {
            'fields': ('student', 'quiz', 'score', 'is_passed')
        }),
        ('Tiempo', {
            'fields': ('time_taken_minutes', 'started_at', 'completed_at')
        }),
    )

class ActivitySubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'title', 'is_submitted', 'grade', 'submitted_at']
    list_filter = ['is_submitted', 'lesson__module__course', 'submitted_at']
    search_fields = ['student__student__first_name', 'student__student__last_name', 'title', 'lesson__title']
    readonly_fields = ['submitted_at']
    
    fieldsets = (
        ('Entrega', {
            'fields': ('student', 'lesson', 'title', 'description')
        }),
        ('Archivos', {
            'fields': ('file', 'image', 'url')
        }),
        ('Evaluación', {
            'fields': ('is_submitted', 'grade', 'feedback', 'submitted_at')
        }),
    )

class UploadAdmin(TranslationAdmin):
    list_display = ['title', 'course', 'upload_time']
    list_filter = ['course', 'upload_time']
    search_fields = ['title', 'course__title']

class LessonBlockAdmin(admin.ModelAdmin):
    list_display = ['lesson', 'block_type', 'title', 'order', 'is_active']
    list_filter = ['block_type', 'is_active', 'lesson__module__course']
    search_fields = ['title', 'lesson__title', 'text_content']
    ordering = ['lesson', 'order']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('lesson', 'block_type', 'title', 'order')
        }),
        ('Contenido de Texto', {
            'fields': ('text_content',),
            'classes': ('collapse',)
        }),
        ('Contenido Multimedia', {
            'fields': ('video_url', 'video_file', 'audio_file', 'image', 'file'),
            'classes': ('collapse',)
        }),
        ('Contenido Embebido', {
            'fields': ('embed_url', 'embed_code'),
            'classes': ('collapse',)
        }),
        ('Configuración Visual', {
            'fields': ('width', 'height', 'background_color')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
    )

class QuizBlockOptionInline(admin.TabularInline):
    model = QuizBlockOption
    extra = 4
    fields = ('option_text', 'is_correct', 'order')

class QuizBlockQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'quiz_block', 'question_type', 'order', 'points', 'is_active']
    list_filter = ['quiz_block', 'question_type', 'is_active']
    search_fields = ['question_text']
    ordering = ['quiz_block', 'order']
    
    fieldsets = (
        ('Pregunta', {
            'fields': ('quiz_block', 'question_text', 'question_type', 'explanation', 'order', 'points')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
    )
    
    inlines = [QuizBlockOptionInline]

class QuizBlockQuestionInline(admin.StackedInline):
    model = QuizBlockQuestion
    extra = 1
    fields = ('question_text', 'question_type', 'explanation', 'order', 'points', 'is_active')

class QuizBlockAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson_block', 'questions_count', 'passing_score', 'time_limit_minutes']
    list_filter = ['lesson_block__lesson__module__course', 'show_results', 'randomize_questions']
    search_fields = ['title', 'description']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('lesson_block', 'title', 'description')
        }),
        ('Configuración del Quiz', {
            'fields': ('passing_score', 'time_limit_minutes', 'attempts_allowed')
        }),
        ('Opciones Avanzadas', {
            'fields': ('show_results', 'randomize_questions')
        }),
    )
    
    inlines = [QuizBlockQuestionInline]

# Registrar modelos
admin.site.register(Program, ProgramAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(CourseAllocation)
admin.site.register(Upload, UploadAdmin)

# Registrar nuevos modelos del sistema de módulos
admin.site.register(Module, ModuleAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(QuizQuestion, QuizQuestionAdmin)
admin.site.register(StudentProgress, StudentProgressAdmin)
admin.site.register(QuizAttempt, QuizAttemptAdmin)
admin.site.register(ActivitySubmission, ActivitySubmissionAdmin)

# Registrar nuevos modelos del sistema de bloques
admin.site.register(LessonBlock, LessonBlockAdmin)
admin.site.register(QuizBlock, QuizBlockAdmin)
admin.site.register(QuizBlockQuestion, QuizBlockQuestionAdmin)
