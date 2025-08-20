from django.http.response import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.views.generic import CreateView, ListView
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.contrib.auth.forms import PasswordChangeForm
from django_filters.views import FilterView
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from core.models import Session, Semester
from course.models import Course
from result.models import TakenCourse
from .decorators import admin_required
from .forms import (
    StaffAddForm,
    StudentAddForm,
    ProfileUpdateForm,
    ParentAddForm,
    ProgramUpdateForm,
    UnifiedUserRegistrationForm,
    StudentEditForm,
    LecturerEditForm,
)
from .models import User, Student, Parent, DepartmentHead
from .filters import LecturerFilter, StudentFilter

# to generate pdf from template we need the following
from django.http import HttpResponse
from django.template.loader import get_template  # to get template which render as pdf
from xhtml2pdf import pisa
from django.template.loader import (
    render_to_string,
)  # to render a template into a string


def validate_username(request):
    username = request.GET.get("username", None)
    data = {"is_taken": User.objects.filter(username__iexact=username).exists()}
    return JsonResponse(data)


def register(request):
    """Registro unificado de usuarios con selección de rol"""
    if request.method == "POST":
        form = UnifiedUserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                user_role = form.cleaned_data.get('user_role')
                role_names = {
                    'student': _('Student'),
                    'lecturer': _('Lecturer'),
                    'parent': _('Parent'),
                    'dep_head': _('Department Head'),
                }
                role_name = role_names.get(user_role, user_role)
                messages.success(request, f"¡Cuenta de {role_name} creada exitosamente! Ya puedes iniciar sesión.")
                return redirect('login')
            except Exception as e:
                messages.error(request, f"Error al crear la cuenta: {str(e)}")
        else:
            # Debug: print form errors to console
            print("Form validation errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UnifiedUserRegistrationForm()
    context = {
        "form": form,
        "base_template": "registration/registration_base.html",
    }
    return render(request, "registration/register.html", context)

def user_count(request):
    """API endpoint para obtener el número de usuarios"""
    from django.http import JsonResponse
    count = User.objects.count()
    return JsonResponse({'count': count})


@login_required
def profile(request):
    """Show profile of any user that fire out the request"""
    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()

    if request.user.is_lecturer:
        # Mostrar todos los cursos asignados al profesor, no solo del semestre actual
        courses = Course.objects.filter(
            allocated_course__lecturer__pk=request.user.id
        )
        return render(
            request,
            "accounts/profile.html",
            {
                "title": request.user.get_full_name,
                "courses": courses,
                "current_session": current_session,
                "current_semester": current_semester,
            },
        )
    elif request.user.is_student:
        level = Student.objects.get(student__pk=request.user.id)
        try:
            parent = Parent.objects.get(student=level)
        except:
            parent = "no parent set"
        # Mostrar todos los cursos del estudiante, no solo del nivel actual
        courses = TakenCourse.objects.filter(
            student__student__id=request.user.id
        )
        context = {
            "title": request.user.get_full_name,
            "parent": parent,
            "courses": courses,
            "level": level,
            "current_session": current_session,
            "current_semester": current_semester,
        }
        return render(request, "accounts/profile.html", context)
    else:
        staff = User.objects.filter(is_lecturer=True)
        return render(
            request,
            "accounts/profile.html",
            {
                "title": request.user.get_full_name,
                "staff": staff,
                "current_session": current_session,
                "current_semester": current_semester,
            },
        )


# function that generate pdf by taking Django template and its context,
def render_to_pdf(template_name, context):
    """Renders a given template to PDF format."""
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="profile.pdf"'  # Set default filename

    template = render_to_string(template_name, context)
    pdf = pisa.CreatePDF(template, dest=response)
    if pdf.err:
        return HttpResponse("We had some problems generating the PDF")

    return response


@login_required
@login_required
def profile_single(request, id):
    """Show profile of any selected user"""
    if request.user.id == id:
        return redirect("/profile/")
    
    # Verificar permisos: solo admin, o profesor viendo sus estudiantes
    if not request.user.is_superuser:
        # Si es profesor, verificar que el estudiante esté en sus cursos
        if request.user.is_lecturer:
            student_user = User.objects.get(pk=id)
            if not student_user.is_student:
                messages.error(request, "No tienes permisos para ver este perfil.")
                return redirect("add_score")
            
            # Verificar que el estudiante esté en algún curso del profesor
            student_courses = TakenCourse.objects.filter(
                student__student__id=id,
                course__allocated_course__lecturer__pk=request.user.id
            )
            if not student_courses.exists():
                messages.error(request, "No tienes permisos para ver este perfil.")
                return redirect("add_score")
        else:
            messages.error(request, "No tienes permisos para ver este perfil.")
            return redirect("add_score")

    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()

    user = User.objects.get(pk=id)
    """
    If download_pdf exists, instead of calling render_to_pdf directly, 
    pass the context dictionary built for the specific user type 
    (lecturer, student, or superuser) to the render_to_pdf function.
    """
    if request.GET.get("download_pdf"):
        if user.is_lecturer:
            courses = Course.objects.filter(allocated_course__lecturer__pk=id).filter(
                semester=current_semester
            )
            context = {
                "title": user.get_full_name,
                "user": user,
                "user_type": "Lecturer",
                "courses": courses,
                "current_session": current_session,
                "current_semester": current_semester,
            }
        elif user.is_student:
            student = Student.objects.get(student__pk=id)
            courses = TakenCourse.objects.filter(
                student__student__id=id, course__level=student.level
            )
            context = {
                "title": user.get_full_name,
                "user": user,
                "user_type": "student",
                "courses": courses,
                "student": student,
                "current_session": current_session,
                "current_semester": current_semester,
            }
        else:
            context = {
                "title": user.get_full_name,
                "user": user,
                "user_type": "superuser",
                "current_session": current_session,
                "current_semester": current_semester,
            }
        return render_to_pdf("pdf/profile_single.html", context)

    else:
        if user.is_lecturer:
            courses = Course.objects.filter(allocated_course__lecturer__pk=id).filter(
                semester=current_semester
            )
            context = {
                "title": user.get_full_name,
                "user": user,
                "user_type": "Lecturer",
                "courses": courses,
                "current_session": current_session,
                "current_semester": current_semester,
            }
            return render(request, "accounts/profile_single.html", context)
        elif user.is_student:
            student = Student.objects.get(student__pk=id)
            courses = TakenCourse.objects.filter(
                student__student__id=id, course__level=student.level
            )
            context = {
                "title": user.get_full_name,
                "user": user,
                "user_type": "student",
                "courses": courses,
                "student": student,
                "current_session": current_session,
                "current_semester": current_semester,
            }
            return render(request, "accounts/profile_single.html", context)
        else:
            context = {
                "title": user.get_full_name,
                "user": user,
                "user_type": "superuser",
                "current_session": current_session,
                "current_semester": current_semester,
            }
            return render(request, "accounts/profile_single.html", context)


@login_required
@admin_required
def admin_panel(request):
    return render(
        request, "setting/admin_panel.html", {"title": request.user.get_full_name}
    )


# ########################################################


# ########################################################
# Setting views
# ########################################################
@login_required
def profile_update(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("profile")
        else:
            messages.error(request, "Please correct the error(s) below.")
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(
        request,
        "setting/profile_info_change.html",
        {
            "title": "Setting",
            "form": form,
        },
    )


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect("profile")
        else:
            messages.error(request, "Please correct the error(s) below. ")
    else:
        form = PasswordChangeForm(request.user)
    return render(
        request,
        "setting/password_change.html",
        {
            "form": form,
        },
    )


# ########################################################


@login_required
@admin_required
def staff_add_view(request):
    """Registro unificado de usuarios con selección de rol"""
    if request.method == "POST":
        form = UnifiedUserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                user_role = form.cleaned_data.get('user_role')
                role_names = {
                    'student': _('Student'),
                    'lecturer': _('Lecturer'),
                    'parent': _('Parent'),
                    'dep_head': _('Department Head'),
                }
                role_name = role_names.get(user_role, user_role)
                messages.success(request, f"¡Cuenta de {role_name} creada exitosamente! Ya puedes iniciar sesión.")
                return redirect('lecturer_list')
            except Exception as e:
                messages.error(request, f"Error al crear la cuenta: {str(e)}")
        else:
            # Debug: print form errors to console
            print("Form validation errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UnifiedUserRegistrationForm(initial={"user_role": "lecturer"})
        # Lock role selection in admin flow
        try:
            form.fields["user_role"].widget.attrs["data-lock-role"] = "true"
            # Asegurar que el valor inicial se establezca correctamente
            form.fields["user_role"].initial = "lecturer"
            # También establecer el valor en el widget
            form.fields["user_role"].widget.attrs["value"] = "lecturer"
        except Exception:
            pass

    context = {
        "title": _("Registrar Profesor"),
        "form": form,
        "base_template": "base.html",
        "use_compact_header": True,
    }
    return render(request, "registration/register.html", context)


@login_required
@admin_required
def student_add_view(request):
    """Registro unificado de usuarios con selección de rol"""
    if request.method == "POST":
        form = UnifiedUserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                user_role = form.cleaned_data.get('user_role')
                role_names = {
                    'student': _('Student'),
                    'lecturer': _('Lecturer'),
                    'parent': _('Parent'),
                    'dep_head': _('Department Head'),
                }
                role_name = role_names.get(user_role, user_role)
                messages.success(request, f"¡Cuenta de {role_name} creada exitosamente! Ya puedes iniciar sesión.")
                return redirect('student_list')
            except Exception as e:
                messages.error(request, f"Error al crear la cuenta: {str(e)}")
        else:
            # Debug: print form errors to console
            print("Form validation errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UnifiedUserRegistrationForm(initial={"user_role": "student"})
        # Lock role selection in admin flow
        try:
            form.fields["user_role"].widget.attrs["data-lock-role"] = "true"
            # Asegurar que el valor inicial se establezca correctamente
            form.fields["user_role"].initial = "student"
            # También establecer el valor en el widget
            form.fields["user_role"].widget.attrs["value"] = "student"
        except Exception:
            pass

    context = {
        "title": _("Registrar Estudiante"),
        "form": form,
        "base_template": "base.html",
        "use_compact_header": True,
    }
    return render(request, "registration/register.html", context)


@login_required
@admin_required
def edit_staff(request, pk):
    instance = get_object_or_404(User, is_lecturer=True, pk=pk)
    if request.method == "POST":
        form = LecturerEditForm(request.POST, request.FILES, instance=instance)
        full_name = instance.get_full_name
        if form.is_valid():
            form.save()
            messages.success(request, f"El profesor {full_name} ha sido actualizado exitosamente.")
            return redirect("lecturer_list")
        else:
            messages.error(request, "Por favor corrige los errores a continuación.")
            # Debug: print form errors to console
            print("Form validation errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = LecturerEditForm(instance=instance)
    return render(
        request,
        "accounts/edit_lecturer.html",
        {
            "title": "Editar Profesor",
            "form": form,
        },
    )


@method_decorator([login_required, admin_required], name="dispatch")
class LecturerFilterView(FilterView):
    filterset_class = LecturerFilter
    queryset = User.objects.filter(is_lecturer=True).select_related()
    template_name = "accounts/lecturer_list.html"
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        total_lecturers = User.objects.filter(is_lecturer=True).count()
        active_lecturers = User.objects.filter(is_lecturer=True, is_active=True).count()
        inactive_lecturers = total_lecturers - active_lecturers
        
        # Estadísticas por género
        male_lecturers = User.objects.filter(is_lecturer=True, gender='M').count()
        female_lecturers = User.objects.filter(is_lecturer=True, gender='F').count()
        
        # Estadísticas por fecha de registro (últimos 30 días)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_lecturers = User.objects.filter(is_lecturer=True, date_joined__gte=thirty_days_ago).count()
        
        # Últimos registros
        latest_lecturers = User.objects.filter(is_lecturer=True).order_by('-date_joined')[:5]
        
        context.update({
            "title": "Profesores",
            "total_lecturers": total_lecturers,
            "active_lecturers": active_lecturers,
            "inactive_lecturers": inactive_lecturers,
            "male_lecturers": male_lecturers,
            "female_lecturers": female_lecturers,
            "recent_lecturers": recent_lecturers,
            "latest_lecturers": latest_lecturers,
            "filter": self.filterset,
        })
        return context


# lecturers list pdf
def render_lecturer_pdf_list(request):
    lecturers = User.objects.filter(is_lecturer=True)
    template_path = "pdf/lecturer_list.html"
    context = {"lecturers": lecturers}
    response = HttpResponse(
        content_type="application/pdf"
    )  # convert the response to pdf
    response["Content-Disposition"] = 'filename="lecturers_list.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)
    # create a pdf
    pisa_status = pisa.CreatePDF(html, dest=response)
    # if error then show some funny view
    if pisa_status.err:
        return HttpResponse("We had some errors <pre>" + html + "</pre>")
    return response


# @login_required
# @lecturer_required
# def delete_staff(request, pk):
#     staff = get_object_or_404(User, pk=pk)
#     staff.delete()
#     return redirect('lecturer_list')


@login_required
@admin_required
def delete_staff(request, pk):
    lecturer = get_object_or_404(User, pk=pk)
    full_name = lecturer.get_full_name
    lecturer.delete()
    messages.success(request, "Lecturer " + full_name + " has been deleted.")
    return redirect("lecturer_list")


# ########################################################


# ########################################################
# Student views
# ########################################################


@login_required
@admin_required
def edit_student(request, pk):
    """Editar estudiante con todos sus campos"""
    instance = get_object_or_404(User, is_student=True, pk=pk)
    if request.method == "POST":
        form = StudentEditForm(request.POST, request.FILES, instance=instance)
        full_name = instance.get_full_name
        if form.is_valid():
            form.save()
            messages.success(request, f"El estudiante {full_name} ha sido actualizado exitosamente.")
            return redirect("student_list")
        else:
            messages.error(request, "Por favor corrige los errores a continuación.")
    else:
        form = StudentEditForm(instance=instance)
    return render(
        request,
        "accounts/edit_student.html",
        {
            "title": "Editar Estudiante",
            "form": form,
        },
    )


@method_decorator([login_required, admin_required], name="dispatch")
class StudentListView(FilterView):
    queryset = Student.objects.all().select_related('student', 'program')
    filterset_class = StudentFilter
    template_name = "accounts/student_list.html"
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        total_students = Student.objects.count()
        active_students = Student.objects.filter(student__is_active=True).count()
        inactive_students = total_students - active_students
        
        # Estadísticas por género
        male_students = Student.objects.filter(student__gender='M').count()
        female_students = Student.objects.filter(student__gender='F').count()
        
        # Estadísticas por nivel
        bachelor_students = Student.objects.filter(level='Bachelor').count()
        master_students = Student.objects.filter(level='Master').count()
        
        # Últimos registros
        recent_students = Student.objects.select_related('student', 'program').order_by('-student__date_joined')[:5]
        
        context.update({
            "title": "Estudiantes",
            "total_students": total_students,
            "active_students": active_students,
            "inactive_students": inactive_students,
            "male_students": male_students,
            "female_students": female_students,
            "bachelor_students": bachelor_students,
            "master_students": master_students,
            "recent_students": recent_students,
            "filter": self.filterset,
        })
        return context


# student list pdf
def render_student_pdf_list(request):
    students = Student.objects.all()
    template_path = "pdf/student_list.html"
    context = {"students": students}
    response = HttpResponse(
        content_type="application/pdf"
    )  # convert the response to pdf
    response["Content-Disposition"] = 'filename="students_list.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)
    # create a pdf
    pisa_status = pisa.CreatePDF(html, dest=response)
    # if error then show some funny view
    if pisa_status.err:
        return HttpResponse("We had some errors <pre>" + html + "</pre>")
    return response


@login_required
@admin_required
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    # full_name = student.user.get_full_name
    student.delete()
    messages.success(request, "El estudiante ha sido eliminado.")
    return redirect("student_list")


@login_required
@admin_required
def edit_student_program(request, pk):

    instance = get_object_or_404(Student, student_id=pk)
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = ProgramUpdateForm(request.POST, request.FILES, instance=instance)
        full_name = user.get_full_name
        if form.is_valid():
            form.save()
            messages.success(request, message=full_name + " program has been updated.")
            url = (
                "/accounts/profile/" + user.id.__str__() + "/detail/"
            )  # Botched job, must optimize
            return redirect(to=url)
        else:
            messages.error(request, "Please correct the error(s) below.")
    else:
        form = ProgramUpdateForm(instance=instance)
    return render(
        request,
        "accounts/edit_student_program.html",
        context={"title": "Edit-program", "form": form, "student": instance},
    )


# ########################################################


class ParentAdd(CreateView):
    model = Parent
    form_class = ParentAddForm
    template_name = "accounts/parent_form.html"


# ########################################################
# Department Head views (simple list + add via unified form)
# ########################################################

@login_required
@admin_required
def dep_head_list_view(request):
    heads = User.objects.filter(is_dep_head=True).order_by('-date_joined')
    return render(request, 'accounts/dep_head_list.html', {
        'title': 'Jefes de Departamento',
        'total_heads': heads.count(),
        'active_heads': heads.filter(is_active=True).count(),
        'inactive_heads': heads.filter(is_active=False).count(),
        'male_heads': heads.filter(gender='M').count(),
        'female_heads': heads.filter(gender='F').count(),
        'recent_heads': heads[:5],
        'heads': heads,
    })


@login_required
@admin_required
def dep_head_add_view(request):
    if request.method == 'POST':
        form = UnifiedUserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                user_role = form.cleaned_data.get('user_role')
                role_names = {
                    'student': _('Student'),
                    'lecturer': _('Lecturer'),
                    'parent': _('Parent'),
                    'dep_head': _('Department Head'),
                }
                role_name = role_names.get(user_role, user_role)
                messages.success(request, f"¡Cuenta de {role_name} creada exitosamente! Ya puedes iniciar sesión.")
                return redirect('dep_head_list')
            except Exception as e:
                messages.error(request, f"Error al crear la cuenta: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UnifiedUserRegistrationForm(initial={'user_role': 'dep_head'})
        try:
            form.fields['user_role'].widget.attrs['data-lock-role'] = 'true'
            form.fields['user_role'].initial = 'dep_head'
            form.fields['user_role'].widget.attrs['value'] = 'dep_head'
        except Exception:
            pass
    return render(request, 'registration/register.html', {
        'title': _('Registrar Jefe de Departamento'),
        'form': form,
        'base_template': 'base.html',
        'use_compact_header': True,
    })


# def parent_add(request):
#     if request.method == 'POST':
#         form = ParentAddForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('student_list')
#     else:
#         form = ParentAddForm(request.POST)
