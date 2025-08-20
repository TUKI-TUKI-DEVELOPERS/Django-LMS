from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Avg, Max, Min, Count, F
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.views.generic import CreateView
from django.core.paginator import Paginator
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django_filters.views import FilterView
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.models import User, Student
from core.models import Session, Semester
from result.models import TakenCourse
from accounts.decorators import lecturer_required, student_required
from .forms import (
    ProgramForm,
    CourseAddForm,
    CourseAllocationForm,
    EditCourseAllocationForm,
    UploadFormFile,
    UploadFormVideo,
    ModuleForm,
    LessonForm,
    LessonContentForm,
    QuizForm,
    QuizQuestionForm,
    QuizOptionForm,
    LessonBlockForm,
    QuizBlockForm,
    QuizBlockQuestionForm,
    QuizBlockOptionForm,
)
from .filters import ProgramFilter, CourseFilter, CourseAllocationFilter
from .models import (
    Program, Course, CourseAllocation, Upload, UploadVideo, Module, Lesson, 
    LessonContent, Quiz, QuizOption, QuizResponse, QuizAttempt, ActivitySubmission, 
    StudentProgress, LessonBlock, QuizBlock, QuizBlockQuestion, QuizBlockOption
)


@method_decorator([login_required, lecturer_required], name="dispatch")
class ProgramFilterView(FilterView):
    filterset_class = ProgramFilter
    template_name = "course/program_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Programas Académicos"
        
        # Agregar información adicional a cada programa
        for program in context['filter'].qs:
            # Contar cursos por programa
            program.course_count = program.course_set.count()
            
            # Contar estudiantes inscritos en el programa
            program.student_count = Student.objects.filter(
                program=program
            ).count()
            
            # Obtener cursos activos del programa
            program.active_courses = program.course_set.filter(is_active=True).count()
            
            # Calcular duración total del programa (suma de duraciones de cursos)
            total_duration = 0
            for course in program.course_set.all():
                if course.duration:
                    total_duration += course.duration
            program.total_duration = total_duration
            
            # Determinar el estado del programa
            if program.course_count == 0:
                program.status = "Sin cursos"
                program.status_color = "text-muted"
            elif program.active_courses == 0:
                program.status = "Inactivo"
                program.status_color = "text-warning"
            else:
                program.status = "Activo"
                program.status_color = "text-success"
        
        return context


@method_decorator([login_required, lecturer_required], name="dispatch")
class CourseFilterView(FilterView):
    filterset_class = CourseFilter
    template_name = "course/course_list.html"
    paginate_by = 12

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Courses"
        return context


@login_required
@lecturer_required
def program_add(request):
    if request.method == "POST":
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, str(request.POST.get("title")) + " programa ha sido creado."
            )
            return redirect("course:programs")
        else:
            messages.error(request, "Por favor corrige el(los) error(es) de abajo.")
    else:
        form = ProgramForm()

    return render(
        request,
        "course/program_add.html",
        {"title": "Agregar Programa", "form": form},
    )


@login_required
def program_detail(request, pk):
    program = Program.objects.get(pk=pk)
    courses = Course.objects.filter(program__pk=pk)
    
    # Agregar información profesional a cada curso
    for course in courses:
        course.professional_info = {}
        if course.duration and course.duration_unit:
            course.professional_info['Duración'] = f"{course.duration} {course.get_duration_unit_display()}"
        if course.modality:
            course.professional_info['Modalidad'] = course.get_modality_display()
        if course.category:
            course.professional_info['Categoría'] = course.get_category_display()
        if course.max_students:
            course.professional_info['Máximo Estudiantes'] = course.max_students
        if course.certification:
            course.professional_info['Certificación'] = "Sí"
        if course.is_active:
            course.professional_info['Estado'] = "Activo"

    return render(
        request,
        "course/program_detail.html",
        {
            "title": program.title,
            "program": program,
            "courses": courses,
        },
    )


@login_required
@lecturer_required
def program_edit(request, pk):
    program = Program.objects.get(pk=pk)

    if request.method == "POST":
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            messages.success(
                request, str(request.POST.get("title")) + " programa ha sido actualizado."
            )
            return redirect("course:programs")
    else:
        form = ProgramForm(instance=program)

    return render(
        request,
        "course/program_add.html",
        {"title": "Editar Programa", "form": form},
    )


@login_required
@lecturer_required
def program_delete(request, pk):
    program = Program.objects.get(pk=pk)
    title = program.title
    program.delete()
    messages.success(request, "Programa " + title + " ha sido eliminado.")

    return redirect("course:programs")


# ########################################################


# ########################################################
# Course views
# ########################################################
@login_required
def course_single(request, slug):
    course = Course.objects.get(slug=slug)
    files = Upload.objects.filter(course__slug=slug)
    videos = UploadVideo.objects.filter(course__slug=slug)

    # lecturers = User.objects.filter(allocated_lecturer__pk=course.id)
    lecturers = CourseAllocation.objects.filter(courses__pk=course.id)

    return render(
        request,
        "course/course_single.html",
        {
            "title": course.title,
            "course": course,
            "files": files,
            "videos": videos,
            "lecturers": lecturers,
            "media_url": settings.MEDIA_ROOT,
        },
    )


@login_required
@lecturer_required
def course_add(request, pk):
    users = User.objects.all()
    if request.method == "POST":
        form = CourseAddForm(request.POST, request.FILES)
        course_name = request.POST.get("title")
        course_code = request.POST.get("code")
        if form.is_valid():
            form.save()
            messages.success(
                request, (course_name + "(" + course_code + ")" + " has been created.")
            )
            return redirect("course:program_detail", pk=request.POST.get("program"))
        else:
            messages.error(request, "Correct the error(s) below.")
    else:
        form = CourseAddForm(initial={"program": Program.objects.get(pk=pk)})

    return render(
        request,
        "course/course_add.html",
        {
            "title": "Add Course",
            "form": form,
            "program": pk,
            "users": users,
        },
    )


@login_required
@lecturer_required
def course_edit(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = CourseAddForm(request.POST, request.FILES, instance=course)
        course_name = request.POST.get("title")
        course_code = request.POST.get("code")
        if form.is_valid():
            form.save()
            messages.success(
                request, (course_name + "(" + course_code + ")" + " ha sido actualizado.")
            )
            return redirect("course:program_detail", pk=request.POST.get("program"))
        else:
            messages.error(request, "Corrige los errores a continuación.")
    else:
        form = CourseAddForm(instance=course)

    return render(
        request,
        "course/course_add.html",
        {
            "title": "Editar Curso",
            # 'form': form, 'program': pk, 'course': pk
            "form": form,
        },
    )


@login_required
@lecturer_required
def course_delete(request, slug):
    course = Course.objects.get(slug=slug)
    # course_name = course.title
    course.delete()
    messages.success(request, "El curso " + course.title + " ha sido eliminado.")

    return redirect("course:program_detail", pk=course.program.id)


# ########################################################


# ########################################################
# Course Allocation
# ########################################################
@method_decorator([login_required], name="dispatch")
class CourseAllocationFormView(CreateView):
    form_class = CourseAllocationForm
    template_name = "course/course_allocation_form.html"

    def get_form_kwargs(self):
        kwargs = super(CourseAllocationFormView, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # if a staff has been allocated a course before update it else create new
        lecturer = form.cleaned_data["lecturer"]
        selected_courses = form.cleaned_data["courses"]
        courses = ()
        for course in selected_courses:
            courses += (course.pk,)
        # print(courses)

        try:
            a = CourseAllocation.objects.get(lecturer=lecturer)
        except:
            a = CourseAllocation.objects.create(lecturer=lecturer)
        for i in range(0, selected_courses.count()):
            a.courses.add(courses[i])
            a.save()
        return redirect("course:course_allocation_view")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Assign Course"
        return context


@method_decorator([login_required], name="dispatch")
class CourseAllocationFilterView(FilterView):
    filterset_class = CourseAllocationFilter
    template_name = "course/course_allocation_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Course Allocations"
        return context


@login_required
@lecturer_required
def edit_allocated_course(request, pk):
    allocated = get_object_or_404(CourseAllocation, pk=pk)
    if request.method == "POST":
        form = EditCourseAllocationForm(request.POST, instance=allocated)
        if form.is_valid():
            form.save()
            messages.success(request, "course assigned has been updated.")
            return redirect("course:course_allocation_view")
    else:
        form = EditCourseAllocationForm(instance=allocated)

    return render(
        request,
        "course/course_allocation_form.html",
        {"title": "Edit Course Allocated", "form": form, "allocated": pk},
    )


@login_required
@lecturer_required
def deallocate_course(request, pk):
    course = CourseAllocation.objects.get(pk=pk)
    course.delete()
    messages.success(request, "successfully deallocate!")
    return redirect("course:course_allocation_view")


# ########################################################


# ########################################################
# File Upload views
# ########################################################
@login_required
@lecturer_required
def handle_file_upload(request, slug):
    course = Course.objects.get(slug=slug)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.course = course
            obj.save()

            messages.success(
                request, (request.POST.get("title") + " ha sido subido exitosamente.")
            )
            return redirect("course:course_single", slug=slug)
    else:
        form = UploadFormFile()
    return render(
        request,
        "upload/upload_file_form.html",
        {"title": "Subir Archivo", "form": form, "course": course},
    )


@login_required
@lecturer_required
def handle_file_edit(request, slug, file_id):
    course = Course.objects.get(slug=slug)
    instance = Upload.objects.get(pk=file_id)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES, instance=instance)
        # file_name = request.POST.get('name')
        if form.is_valid():
            form.save()
            messages.success(
                request, (request.POST.get("title") + " ha sido actualizado exitosamente.")
            )
            return redirect("course:course_single", slug=slug)
    else:
        form = UploadFormFile(instance=instance)

    return render(
        request,
        "upload/upload_file_form.html",
        {"title": instance.title, "form": form, "course": course},
    )


def handle_file_delete(request, slug, file_id):
    file = Upload.objects.get(pk=file_id)
    # file_name = file.name
    file.delete()

    messages.success(request, (file.title + " ha sido eliminado exitosamente."))
    return redirect("course:course_single", slug=slug)


# ########################################################
# Video Upload views
# ########################################################
@login_required
@lecturer_required
def handle_video_upload(request, slug):
    course = Course.objects.get(slug=slug)
    if request.method == "POST":
        form = UploadFormVideo(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.course = course
            obj.save()

            messages.success(
                request, (request.POST.get("title") + " ha sido subido exitosamente.")
            )
            return redirect("course:course_single", slug=slug)
    else:
        form = UploadFormVideo()
    return render(
        request,
        "upload/upload_video_form.html",
        {"title": "Subir Video", "form": form, "course": course},
    )


@login_required
# @lecturer_required
def handle_video_single(request, slug, video_slug):
    course = get_object_or_404(Course, slug=slug)
    video = get_object_or_404(UploadVideo, slug=video_slug)
    return render(request, "upload/video_single.html", {"video": video})


@login_required
@lecturer_required
def handle_video_edit(request, slug, video_slug):
    course = Course.objects.get(slug=slug)
    instance = UploadVideo.objects.get(slug=video_slug)
    if request.method == "POST":
        form = UploadFormVideo(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(
                request, (request.POST.get("title") + " ha sido actualizado exitosamente.")
            )
            return redirect("course:course_single", slug=slug)
    else:
        form = UploadFormVideo(instance=instance)

    return render(
        request,
        "upload/upload_video_form.html",
        {"title": instance.title, "form": form, "course": course},
    )


def handle_video_delete(request, slug, video_slug):
    video = get_object_or_404(UploadVideo, slug=video_slug)
    # video = UploadVideo.objects.get(slug=video_slug)
    video.delete()

    messages.success(request, (video.title + " ha sido eliminado exitosamente."))


# ########################################################


# ########################################################
# Course Registration
# ########################################################
@login_required
@student_required
def course_registration(request):
    if request.method == "POST":
        student = Student.objects.get(student__pk=request.user.id)
        ids = ()
        data = request.POST.copy()
        data.pop("csrfmiddlewaretoken", None)  # remove csrf_token
        
        # Validar que se seleccionaron cursos
        if not data.keys():
            messages.warning(request, "Por favor selecciona al menos un curso para registrar.")
            return redirect("course:course_registration")
        
        courses_to_register = []
        for key in data.keys():
            try:
                course = Course.objects.get(pk=key)
                # Verificar si ya está registrado para evitar duplicados
                if not TakenCourse.objects.filter(student=student, course=course).exists():
                    courses_to_register.append(course)
                else:
                    messages.warning(request, f"El curso '{course.title}' ya está registrado.")
            except Course.DoesNotExist:
                messages.error(request, f"Curso con ID {key} no encontrado.")
                continue
        
        # Registrar los cursos válidos
        if courses_to_register:
            for course in courses_to_register:
                obj = TakenCourse.objects.create(student=student, course=course)
                obj.save()
            
            total_credits = sum(course.credit for course in courses_to_register)
            course_names = ", ".join([course.title for course in courses_to_register])
            
            if len(courses_to_register) == 1:
                messages.success(request, f"¡Curso '{course_names}' registrado exitosamente! ({total_credits} créditos)")
            else:
                messages.success(request, f"¡{len(courses_to_register)} cursos registrados exitosamente! ({total_credits} créditos total)")
        
        return redirect("course:course_registration")
    else:
        current_semester = Semester.objects.filter(is_current_semester=True).first()
        if not current_semester:
            messages.error(request, "No se encontró un semestre activo.")
            return render(request, "course/course_registration.html")

        student = get_object_or_404(Student, student__id=request.user.id)
        taken_courses = TakenCourse.objects.filter(student__student__id=request.user.id).select_related('course')
        t = ()
        for i in taken_courses:
            t += (i.course.pk,)

        # Obtener cursos disponibles para el semestre actual
        courses = (
            Course.objects.filter(
                program__pk=student.program.id,
                level=student.level,
                semester=current_semester.semester,
            )
            .exclude(id__in=t)
            .order_by("year")
            .select_related('program')
        )
        
        # Obtener todos los cursos del programa para estadísticas
        all_courses = Course.objects.filter(
            level=student.level, 
            program__pk=student.program.id
        ).select_related('program')

        # Cursos ya registrados
        registered_courses = Course.objects.filter(level=student.level).filter(id__in=t).select_related('program')

        # Estados del registro
        no_course_is_registered = registered_courses.count() == 0
        all_courses_are_registered = registered_courses.count() == all_courses.count()

        # Calcular estadísticas por semestre
        first_semester_courses = courses.filter(semester="First")
        second_semester_courses = courses.filter(semester="Second")
        
        total_first_semester_credit = sum(course.credit for course in first_semester_courses)
        total_sec_semester_credit = sum(course.credit for course in second_semester_courses)
        total_registered_credit = sum(course.credit for course in registered_courses)
        
        # Calcular estadísticas generales
        total_available_credits = sum(course.credit for course in courses)
        total_program_credits = sum(course.credit for course in all_courses)
        progress_percentage = (total_registered_credit / total_program_credits * 100) if total_program_credits > 0 else 0
        
        # Agregar información profesional a cada curso
        for course in courses:
            course.professional_info = {}
            if course.duration and course.duration_unit:
                course.professional_info['Duración'] = f"{course.duration} {course.get_duration_unit_display()}"
            if course.modality:
                course.professional_info['Modalidad'] = course.get_modality_display()
            if course.category:
                course.professional_info['Categoría'] = course.get_category_display()
            if course.max_students:
                course.professional_info['Máximo Estudiantes'] = course.max_students
            if course.certification:
                course.professional_info['Certificación'] = "Sí"
            if course.is_active:
                course.professional_info['Estado'] = "Activo"
            
            # Contar materiales disponibles
            course.materials_count = course.upload_set.count() + course.uploadvideo_set.count()
        
        # Agregar información a cursos registrados
        for course in registered_courses:
            course.materials_count = course.upload_set.count() + course.uploadvideo_set.count()
            
            # Información profesional
            course.professional_info = {}
            if course.duration and course.duration_unit:
                course.professional_info['Duración'] = f"{course.duration} {course.get_duration_unit_display()}"
            if course.modality:
                course.professional_info['Modalidad'] = course.get_modality_display()
            if course.category:
                course.professional_info['Categoría'] = course.get_category_display()
            if course.max_students:
                course.professional_info['Máximo Estudiantes'] = course.max_students
            if course.certification:
                course.professional_info['Certificación'] = "Sí"
            if course.is_active:
                course.professional_info['Estado'] = "Activo"

        context = {
            "is_calender_on": True,
            "all_courses_are_registered": all_courses_are_registered,
            "no_course_is_registered": no_course_is_registered,
            "current_semester": current_semester,
            "courses": courses,
            "first_semester_courses": first_semester_courses,
            "second_semester_courses": second_semester_courses,
            "total_first_semester_credit": total_first_semester_credit,
            "total_sec_semester_credit": total_sec_semester_credit,
            "registered_courses": registered_courses,
            "total_registered_credit": total_registered_credit,
            "total_available_credits": total_available_credits,
            "total_program_credits": total_program_credits,
            "progress_percentage": round(progress_percentage, 1),
            "student": student,
            "courses_count": len(courses),
            "registered_count": len(registered_courses),
        }
        return render(request, "course/course_registration.html", context)


@login_required
@student_required
def course_drop(request):
    if request.method == "POST":
        student = Student.objects.get(student__pk=request.user.id)
        data = request.POST.copy()
        data.pop("csrfmiddlewaretoken", None)  # remove csrf_token
        
        # Validar que se seleccionaron cursos
        if not data.keys():
            messages.warning(request, "Por favor selecciona al menos un curso para eliminar.")
            return redirect("course:course_registration")
        
        courses_to_drop = []
        for key in data.keys():
            try:
                course = Course.objects.get(pk=key)
                # Verificar si está registrado
                taken_course = TakenCourse.objects.filter(student=student, course=course).first()
                if taken_course:
                    courses_to_drop.append(course)
                else:
                    messages.warning(request, f"El curso '{course.title}' no está registrado.")
            except Course.DoesNotExist:
                messages.error(request, f"Curso con ID {key} no encontrado.")
                continue
        
        # Eliminar los cursos válidos
        if courses_to_drop:
            for course in courses_to_drop:
                obj = TakenCourse.objects.get(student=student, course=course)
                obj.delete()
            
            total_credits = sum(course.credit for course in courses_to_drop)
            course_names = ", ".join([course.title for course in courses_to_drop])
            
            if len(courses_to_drop) == 1:
                messages.success(request, f"¡Curso '{course_names}' eliminado exitosamente! ({total_credits} créditos)")
            else:
                messages.success(request, f"¡{len(courses_to_drop)} cursos eliminados exitosamente! ({total_credits} créditos total)")
        
        return redirect("course:course_registration")
    else:
        return redirect("course:course_registration")


# ########################################################


@login_required
def user_course_list(request):
    if request.user.is_lecturer:
        courses = Course.objects.filter(allocated_course__lecturer__pk=request.user.id)
        
        # Agregar información adicional para cada curso
        for course in courses:
            course.student_count = course.taken_courses.count()
            course.materials_count = course.upload_set.count() + course.uploadvideo_set.count()
            
        return render(request, "course/user_course_list.html", {"courses": courses})

    elif request.user.is_student:
        student = Student.objects.get(student__pk=request.user.id)
        taken_courses = TakenCourse.objects.filter(
            student__student__id=student.student.id
        ).select_related('course', 'course__program')
        
        # Obtener todos los cursos disponibles para el estudiante
        all_courses = Course.objects.filter(
            level=student.level,
            program__pk=student.program.id
        ).select_related('program')
        
        # Calcular estadísticas del estudiante
        total_credits_registered = sum(course.course.credit for course in taken_courses)
        total_credits_available = sum(course.credit for course in all_courses)
        progress_percentage = (total_credits_registered / total_credits_available * 100) if total_credits_available > 0 else 0
        
        # Calcular GPA actual
        total_points = 0
        total_credits = 0
        for taken_course in taken_courses:
            if taken_course.point > 0:
                total_points += taken_course.point * taken_course.course.credit
                total_credits += taken_course.course.credit
        
        current_gpa = (total_points / total_credits) if total_credits > 0 else 0
        
        # Agregar información detallada a cada curso tomado
        for taken_course in taken_courses:
            course = taken_course.course
            
            # Información de materiales
            course.materials_count = course.upload_set.count() + course.uploadvideo_set.count()
            course.documents_count = course.upload_set.count()
            course.videos_count = course.uploadvideo_set.count()
            
            # Información de progreso
            if taken_course.total > 0:
                course.progress_percentage = min((taken_course.total / 100) * 100, 100)
            else:
                course.progress_percentage = 0
                
            # Estado del curso
            if taken_course.grade:
                course.status = 'completed'
                course.status_text = f'Completado - {taken_course.grade}'
            elif taken_course.total > 0:
                course.status = 'in_progress'
                course.status_text = 'En Progreso'
            else:
                course.status = 'registered'
                course.status_text = 'Registrado'
                
            # Información profesional del curso
            course.professional_info = {}
            if course.duration and course.duration_unit:
                course.professional_info['Duración'] = f"{course.duration} {course.get_duration_unit_display()}"
            if course.modality:
                course.professional_info['Modalidad'] = course.get_modality_display()
            if course.category:
                course.professional_info['Categoría'] = course.get_category_display()
            if course.max_students:
                course.professional_info['Máximo Estudiantes'] = course.max_students
            if course.certification:
                course.professional_info['Certificación'] = "Sí"
            if course.is_active:
                course.professional_info['Estado'] = "Activo"
        
        # Agregar información a cursos disponibles
        for course in all_courses:
            course.is_registered = course.taken_courses.filter(student=student).exists()
            course.materials_count = course.upload_set.count() + course.uploadvideo_set.count()
            
            # Información profesional
            course.professional_info = {}
            if course.duration and course.duration_unit:
                course.professional_info['Duración'] = f"{course.duration} {course.get_duration_unit_display()}"
            if course.modality:
                course.professional_info['Modalidad'] = course.get_modality_display()
            if course.category:
                course.professional_info['Categoría'] = course.get_category_display()
            if course.max_students:
                course.professional_info['Máximo Estudiantes'] = course.max_students
            if course.certification:
                course.professional_info['Certificación'] = "Sí"
            if course.is_active:
                course.professional_info['Estado'] = "Activo"

        context = {
            "student": student,
            "taken_courses": taken_courses,
            "courses": all_courses,
            "total_credits_registered": total_credits_registered,
            "total_credits_available": total_credits_available,
            "progress_percentage": round(progress_percentage, 1),
            "current_gpa": round(current_gpa, 2),
            "courses_count": len(taken_courses),
            "total_courses_available": len(all_courses),
        }
        
        return render(request, "course/user_course_list.html", context)

    else:
        return render(request, "course/user_course_list.html")


# Nuevas vistas para el sistema de módulos
@login_required
def course_modules(request, slug):
    """Vista para mostrar los módulos de un curso"""
    course = get_object_or_404(Course, slug=slug)
    modules = course.modules.filter(is_active=True).prefetch_related('lessons')
    
    # Calcular progreso del estudiante si está logueado como estudiante
    student_progress = None
    if request.user.is_student:
        student = Student.objects.get(student__pk=request.user.id)
        student_progress = StudentProgress.objects.filter(
            student=student,
            lesson__module__course=course
        ).select_related('lesson', 'lesson__module')
    
    context = {
        'course': course,
        'modules': modules,
        'student_progress': student_progress,
    }
    
    return render(request, "course/course_modules.html", context)


@login_required
def module_detail(request, slug, module_id):
    """Vista para mostrar el detalle de un módulo"""
    course = get_object_or_404(Course, slug=slug)
    module = get_object_or_404(Module, id=module_id, course=course, is_active=True)
    
    # Mostrar todas las lecciones, no solo las activas
    lessons = module.lessons.all().prefetch_related('content').order_by('order')
    
    # Calcular progreso del estudiante si está logueado como estudiante
    student_progress = None
    if request.user.is_student:
        student = Student.objects.get(student__pk=request.user.id)
        student_progress = StudentProgress.objects.filter(
            student=student,
            lesson__module=module
        ).select_related('lesson')
    
    context = {
        'course': course,
        'module': module,
        'lessons': lessons,
        'student_progress': student_progress,
    }
    
    return render(request, "course/module_detail.html", context)


@login_required
def lesson_detail(request, slug, module_id, lesson_id):
    """Vista para mostrar el detalle de una lección"""
    course = get_object_or_404(Course, slug=slug)
    module = get_object_or_404(Module, id=module_id, course=course, is_active=True)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module, is_active=True)
    
    # Obtener contenido de la lección (sistema antiguo)
    try:
        content = lesson.content
    except LessonContent.DoesNotExist:
        content = None
    
    # Obtener bloques de contenido de la lección (sistema nuevo)
    blocks = lesson.blocks.filter(is_active=True).order_by('order')
    
    # Obtener progreso del estudiante si está logueado como estudiante
    student_progress = None
    if request.user.is_student:
        student = Student.objects.get(student__pk=request.user.id)
        student_progress, created = StudentProgress.objects.get_or_create(
            student=student,
            lesson=lesson,
            defaults={'is_completed': False}
        )
    
    # Obtener cuestionario si la lección es de tipo quiz
    quiz = None
    if lesson.lesson_type == 'quiz':
        try:
            quiz = lesson.quiz
        except Quiz.DoesNotExist:
            pass
    
    # Obtener entrega de actividad si la lección es de tipo activity
    activity_submission = None
    if lesson.lesson_type == 'activity' and request.user.is_student:
        student = Student.objects.get(student__pk=request.user.id)
        try:
            activity_submission = ActivitySubmission.objects.get(
                student=student,
                lesson=lesson
            )
        except ActivitySubmission.DoesNotExist:
            pass
    
    context = {
        'course': course,
        'module': module,
        'lesson': lesson,
        'content': content,
        'blocks': blocks,  # Agregar bloques al contexto
        'student_progress': student_progress,
        'quiz': quiz,
        'activity_submission': activity_submission,
    }
    
    return render(request, "course/lesson_detail.html", context)


@login_required
@student_required
def mark_lesson_complete(request, slug, module_id, lesson_id):
    """Vista para marcar una lección como completada"""
    if request.method == 'POST':
        course = get_object_or_404(Course, slug=slug)
        module = get_object_or_404(Module, id=module_id, course=course)
        lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
        student = Student.objects.get(student__pk=request.user.id)
        
        # Actualizar o crear progreso del estudiante
        progress, created = StudentProgress.objects.get_or_create(
            student=student,
            lesson=lesson,
            defaults={'is_completed': True}
        )
        
        if not created:
            progress.is_completed = True
            progress.save()
        
        messages.success(request, f"Lección '{lesson.title}' marcada como completada.")
        return redirect('course:lesson_detail', slug=slug, module_id=module_id, lesson_id=lesson_id)
    
    return redirect('course:lesson_detail', slug=slug, module_id=module_id, lesson_id=lesson_id)


@login_required
@student_required
def submit_activity(request, slug, module_id, lesson_id):
    """Vista para enviar una actividad práctica"""
    if request.method == 'POST':
        course = get_object_or_404(Course, slug=slug)
        module = get_object_or_404(Module, id=module_id, course=course)
        lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
        student = Student.objects.get(student__pk=request.user.id)
        
        # Obtener datos del formulario
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')
        image = request.FILES.get('image')
        url = request.POST.get('url')
        
        if not title:
            messages.error(request, "El título es obligatorio.")
            return redirect('course:lesson_detail', slug=slug, module_id=module_id, lesson_id=lesson_id)
        
        # Crear o actualizar entrega
        submission, created = ActivitySubmission.objects.get_or_create(
            student=student,
            lesson=lesson,
            defaults={
                'title': title,
                'description': description,
                'file': file,
                'image': image,
                'url': url,
                'is_submitted': True
            }
        )
        
        if not created:
            submission.title = title
            submission.description = description
            if file:
                submission.file = file
            if image:
                submission.image = image
            submission.url = url
            submission.is_submitted = True
            submission.save()
        
        messages.success(request, "Actividad enviada exitosamente.")
        return redirect('course:lesson_detail', slug=slug, module_id=module_id, lesson_id=lesson_id)
    
    return redirect('course:lesson_detail', slug=slug, module_id=module_id, lesson_id=lesson_id)


@login_required
@student_required
def take_quiz(request, slug, module_id, lesson_id):
    """Vista para tomar un cuestionario"""
    course = get_object_or_404(Course, slug=slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    student = Student.objects.get(student__pk=request.user.id)
    
    try:
        quiz = lesson.quiz
    except Quiz.DoesNotExist:
        messages.error(request, "No se encontró el cuestionario.")
        return redirect('course:lesson_detail', slug=slug, module_id=module_id, lesson_id=lesson_id)
    
    if request.method == 'POST':
        # Procesar respuestas del cuestionario
        score = 0
        total_points = 0
        responses = []
        
        for question in quiz.questions.filter(is_active=True):
            total_points += question.points
            answer = request.POST.get(f'question_{question.id}')
            
            if question.question_type == 'multiple_choice':
                try:
                    selected_option = QuizOption.objects.get(id=answer, question=question)
                    if selected_option.is_correct:
                        score += question.points
                    
                    # Guardar respuesta
                    response = QuizResponse.objects.create(
                        attempt=None,  # Se actualizará después
                        question=question,
                        selected_option=selected_option,
                        is_correct=selected_option.is_correct,
                        points_earned=question.points if selected_option.is_correct else 0
                    )
                    responses.append(response)
                except QuizOption.DoesNotExist:
                    pass
            elif question.question_type == 'true_false':
                is_correct = answer == 'true'  # Asumiendo que 'true' es la respuesta correcta
                if is_correct:
                    score += question.points
                
                # Guardar respuesta
                response = QuizResponse.objects.create(
                    attempt=None,  # Se actualizará después
                    question=question,
                    text_response=answer,
                    is_correct=is_correct,
                    points_earned=question.points if is_correct else 0
                )
                responses.append(response)
            else:
                # Para preguntas de texto, guardar respuesta sin evaluar
                response = QuizResponse.objects.create(
                    attempt=None,  # Se actualizará después
                    question=question,
                    text_response=answer,
                    is_correct=False,  # Requiere revisión manual
                    points_earned=0
                )
                responses.append(response)
        
        # Calcular puntuación final
        final_score = (score / total_points * 100) if total_points > 0 else 0
        
        # Crear intento del cuestionario
        attempt = QuizAttempt.objects.create(
            student=student,
            quiz=quiz,
            score=final_score,
            completed_at=timezone.now()
        )
        
        # Actualizar respuestas con el intento
        for response in responses:
            response.attempt = attempt
            response.save()
        
        # Marcar lección como completada si aprobó
        if final_score >= quiz.passing_score:
            progress, created = StudentProgress.objects.get_or_create(
                student=student,
                lesson=lesson,
                defaults={'is_completed': True}
            )
            if not created:
                progress.is_completed = True
                progress.save()
        
        messages.success(request, f"Cuestionario completado. Puntuación: {final_score:.1f}%")
        return redirect('course:lesson_detail', slug=slug, module_id=module_id, lesson_id=lesson_id)
    
    context = {
        'course': course,
        'module': module,
        'lesson': lesson,
        'quiz': quiz,
    }
    
    return render(request, "course/take_quiz.html", context)


# Vistas para profesores y administradores
@login_required
@lecturer_required
def module_create(request, slug):
    course = get_object_or_404(Course, slug=slug)
    
    if request.method == 'POST':
        form = ModuleForm(request.POST, request.FILES)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            
            # Asignar automáticamente el siguiente orden disponible
            if not module.order:
                last_module = Module.objects.filter(course=course).order_by('-order').first()
                module.order = (last_module.order + 1) if last_module else 1
            
            module.save()
            messages.success(request, f"Módulo '{module.title}' creado exitosamente.")
            return redirect('course:course_modules', slug=slug)
        else:
            messages.error(request, "Por favor corrige los errores a continuación.")
    else:
        form = ModuleForm()
    
    context = {
        'course': course,
        'form': form,
        'title': 'Crear Módulo',
    }
    return render(request, 'course/module_form.html', context)


@login_required
@lecturer_required
def module_edit(request, slug, module_id):
    course = get_object_or_404(Course, slug=slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    if request.method == 'POST':
        form = ModuleForm(request.POST, request.FILES, instance=module)
        if form.is_valid():
            form.save()
            messages.success(request, f"Módulo '{module.title}' actualizado exitosamente.")
            return redirect('course:course_modules', slug=slug)
        else:
            messages.error(request, "Por favor corrige los errores a continuación.")
    else:
        form = ModuleForm(instance=module)
    
    context = {
        'course': course,
        'module': module,
        'form': form,
        'title': 'Editar Módulo',
    }
    return render(request, 'course/module_form.html', context)


@login_required
@lecturer_required
def module_delete(request, slug, module_id):
    course = get_object_or_404(Course, slug=slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    if request.method == 'POST':
        module_title = module.title
        module.delete()
        messages.success(request, f"Módulo '{module_title}' eliminado exitosamente.")
        return redirect('course:course_modules', slug=slug)
    
    context = {
        'course': course,
        'module': module,
        'title': 'Eliminar Módulo',
    }
    return render(request, 'course/module_confirm_delete.html', context)


@login_required
@lecturer_required
def lesson_create(request, slug, module_id):
    course = get_object_or_404(Course, slug=slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.module = module
            
            # Asignar automáticamente el siguiente orden disponible
            if not lesson.order:
                last_lesson = Lesson.objects.filter(module=module).order_by('-order').first()
                lesson.order = (last_lesson.order + 1) if last_lesson else 1
            
            lesson.save()
            messages.success(request, f"Lección '{lesson.title}' creada exitosamente.")
            # Redirigir al canvas de la lección para agregar contenido
            return redirect('course:lesson_canvas', slug=slug, module_id=module_id, lesson_id=lesson.id)
        else:
            messages.error(request, "Por favor corrige los errores a continuación.")
    else:
        form = LessonForm()
    
    context = {
        'course': course,
        'module': module,
        'form': form,
        'title': 'Crear Lección',
    }
    return render(request, 'course/lesson_form.html', context)


@login_required
@lecturer_required
def lesson_canvas(request, slug, module_id, lesson_id):
    """Vista del canvas avanzado para editar contenido de lecciones"""
    course = get_object_or_404(Course, slug=slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    
    # Obtener todos los bloques de contenido de la lección
    blocks = lesson.blocks.filter(is_active=True).order_by('order')
    
    context = {
        'course': course,
        'module': module,
        'lesson': lesson,
        'blocks': blocks,
        'title': f'Editor de Contenido - {lesson.title}',
    }
    return render(request, 'course/lesson_canvas.html', context)


@login_required
@lecturer_required
def block_create(request, slug, module_id, lesson_id):
    """Vista para crear un nuevo bloque de lección."""
    try:
        # Obtener objetos necesarios
        course = get_object_or_404(Course, slug=slug)
        module = get_object_or_404(Module, id=module_id, course=course)
        lesson = get_object_or_404(Lesson, id=lesson_id, module=module)

        # Verificar que el usuario tiene permisos para editar el curso
        if not course.user_can_edit(request.user):
            messages.error(request, _("No tienes permisos para editar este curso."))
            return JsonResponse({
                'success': False,
                'message': _("No tienes permisos para editar este curso.")
            }, status=403)

        if request.method != 'POST':
            return JsonResponse({
                'success': False,
                'message': _("Método no permitido")
            }, status=405)

        # Validar formulario
        form = LessonBlockForm(request.POST, request.FILES)
        if not form.is_valid():
            error_messages = [f"{field}: {error}" for field, errors in form.errors.items() for error in errors]
            return JsonResponse({
                'success': False,
                'errors': form.errors,
                'error_messages': error_messages
            })

        # Crear y configurar el bloque
        block = form.save(commit=False)
        block.lesson = lesson
        block.is_active = True

        # Procesar URLs embebibles según el tipo
        from .utils import get_video_embed_url, get_generic_embed_url
        if block.block_type == 'video' and block.video_url:
            block.video_url = get_video_embed_url(block.video_url)
        if block.block_type in ['embed', 'presentation'] and block.embed_url:
            block.embed_url = get_generic_embed_url(block.embed_url)

        # Guardar el bloque (el orden se asigna automáticamente en el modelo)
        block.save()

        # Crear quiz si es necesario
        quiz_block = None
        if block.block_type == 'quiz':
            quiz_block = QuizBlock.objects.create(
                lesson_block=block,
                title=request.POST.get('quiz_title', _('Nuevo Cuestionario')),
                description=request.POST.get('quiz_description', ''),
                passing_score=int(request.POST.get('passing_score', 70)),
                time_limit_minutes=int(request.POST.get('time_limit_minutes', 0)),
                attempts_allowed=int(request.POST.get('attempts_allowed', 1)),
                show_results=request.POST.get('show_results', 'on') == 'on',
                randomize_questions=request.POST.get('randomize_questions', '') == 'on'
            )

        # Preparar respuesta exitosa
        response_data = {
            'success': True,
            'message': _(f"Bloque de {block.get_block_type_display()} creado exitosamente."),
            'block': {
                'id': block.id,
                'type': block.block_type,
                'title': block.title,
                'order': block.order
            }
        }

        # Agregar info del quiz si existe
        if quiz_block:
            response_data['block']['quiz'] = {
                'id': quiz_block.id,
                'title': quiz_block.title
            }

        messages.success(request, response_data['message'])
        return JsonResponse(response_data)

    except Exception as e:
        error_msg = str(e)
        messages.error(request, _(f"Error al crear el bloque: {error_msg}"))
        return JsonResponse({
            'success': False,
            'error': error_msg
        }, status=500)


@login_required
@lecturer_required  
def block_edit(request, slug, module_id, lesson_id, block_id):
    """Vista para editar un bloque de contenido"""
    course = get_object_or_404(Course, slug=slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    block = get_object_or_404(LessonBlock, id=block_id, lesson=lesson)
    
    if request.method == 'POST':
        form = LessonBlockForm(request.POST, request.FILES, instance=block)
        if form.is_valid():
            form.save()
            
            # Si es un bloque de quiz, actualizar también el QuizBlock
            if block.block_type == 'quiz' and hasattr(block, 'quiz_block'):
                quiz_block = block.quiz_block
                quiz_block.title = request.POST.get('quiz_title', quiz_block.title)
                quiz_block.description = request.POST.get('quiz_description', quiz_block.description)
                quiz_block.passing_score = request.POST.get('passing_score', quiz_block.passing_score)
                quiz_block.time_limit_minutes = request.POST.get('time_limit_minutes', quiz_block.time_limit_minutes)
                quiz_block.attempts_allowed = request.POST.get('attempts_allowed', quiz_block.attempts_allowed)
                quiz_block.show_results = request.POST.get('show_results') == 'on'
                quiz_block.randomize_questions = request.POST.get('randomize_questions') == 'on'
                quiz_block.save()
            
            messages.success(request, f"Bloque de {block.get_block_type_display()} actualizado exitosamente.")
            return JsonResponse({'success': True, 'redirect': f'/es/programs/course/{slug}/module/{module_id}/lesson/{lesson_id}/canvas/'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
@lecturer_required
def block_delete(request, slug, module_id, lesson_id, block_id):
    """Vista para eliminar un bloque de contenido"""
    course = get_object_or_404(Course, slug=slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    block = get_object_or_404(LessonBlock, id=block_id, lesson=lesson)
    
    if request.method == 'POST':
        block_type = block.get_block_type_display()
        block.delete()
        messages.success(request, f"Bloque de {block_type} eliminado exitosamente.")
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
@lecturer_required
def block_reorder(request, slug, module_id, lesson_id):
    """Vista para reordenar bloques de contenido"""
    course = get_object_or_404(Course, slug=slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    
    if request.method == 'POST':
        block_ids = request.POST.getlist('block_ids[]')
        for index, block_id in enumerate(block_ids):
            try:
                block = LessonBlock.objects.get(id=block_id, lesson=lesson)
                block.order = index + 1
                block.save()
            except LessonBlock.DoesNotExist:
                continue
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
@lecturer_required
def lesson_edit(request, slug, module_id, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, f"Lección '{lesson.title}' actualizada exitosamente.")
            return redirect('course:module_detail', slug=slug, module_id=module_id)
        else:
            messages.error(request, "Por favor corrige los errores a continuación.")
    else:
        form = LessonForm(instance=lesson)
    
    context = {
        'course': course,
        'module': module,
        'lesson': lesson,
        'form': form,
        'title': 'Editar Lección',
    }
    return render(request, 'course/lesson_form.html', context)


@login_required
@lecturer_required
def lesson_delete(request, slug, module_id, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    
    if request.method == 'POST':
        lesson_title = lesson.title
        lesson.delete()
        messages.success(request, f"Lección '{lesson_title}' eliminada exitosamente.")
        return redirect('course:module_detail', slug=slug, module_id=module_id)
    
    context = {
        'course': course,
        'module': module,
        'lesson': lesson,
        'title': 'Eliminar Lección',
    }
    return render(request, 'course/lesson_confirm_delete.html', context)


@login_required
@lecturer_required
def lesson_reactivate(request, slug, module_id, lesson_id):
    """Vista para reactivar una lección inactiva"""
    course = get_object_or_404(Course, slug=slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    
    if request.method == 'POST':
        lesson.is_active = True
        lesson.save()
        messages.success(request, f"Lección '{lesson.title}' reactivada exitosamente.")
        return redirect('course:module_detail', slug=slug, module_id=module_id)
    
    context = {
        'course': course,
        'module': module,
        'lesson': lesson,
        'title': 'Reactivar Lección',
    }
    return render(request, 'course/lesson_confirm_reactivate.html', context)


@login_required
@lecturer_required
def lesson_deactivate(request, slug, module_id, lesson_id):
    """Vista para desactivar una lección activa"""
    course = get_object_or_404(Course, slug=slug)
    module = get_object_or_404(Module, id=module_id, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module=module)
    
    if request.method == 'POST':
        lesson.is_active = False
        lesson.save()
        messages.success(request, f"Lección '{lesson.title}' desactivada exitosamente.")
        return redirect('course:module_detail', slug=slug, module_id=module_id)
    
    context = {
        'course': course,
        'module': module,
        'lesson': lesson,
        'title': 'Desactivar Lección',
    }
    return render(request, 'course/lesson_confirm_deactivate.html', context)
