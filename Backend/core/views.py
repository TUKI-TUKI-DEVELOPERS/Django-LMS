from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from accounts.decorators import admin_required, lecturer_required
from accounts.models import User, Student
from .forms import SessionForm, SemesterForm, NewsAndEventsForm
from .models import NewsAndEvents, ActivityLog, Session, Semester


# ########################################################
# News & Events
# ########################################################
@login_required
def home_view(request):
    items = NewsAndEvents.objects.all().order_by("-updated_date")
    context = {
        "title": "News & Events",
        "items": items,
    }
    return render(request, "core/index.html", context)


@login_required
def dashboard_view(request):
    logs = ActivityLog.objects.all().order_by("-created_at")[:10]
    gender_count = Student.get_gender_count()
    context = {
        "student_count": User.objects.get_student_count(),
        "lecturer_count": User.objects.get_lecturer_count(),
        "superuser_count": User.objects.get_superuser_count(),
        "males_count": gender_count["M"],
        "females_count": gender_count["F"],
        "logs": logs,
    }
    return render(request, "core/dashboard.html", context)


@login_required
def post_add(request):
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST, request.FILES)
        title = request.POST.get("title")
        if form.is_valid():
            form.save()

            messages.success(request, (title + " ha sido subido exitosamente."))
            return redirect("home")
        else:
            messages.error(request, "Por favor corrige los errores a continuación.")
    else:
        form = NewsAndEventsForm()
    return render(
        request,
        "core/post_add.html",
        {
            "title": "Agregar Publicación",
            "form": form,
        },
    )


@login_required
@lecturer_required
def edit_post(request, pk):
    instance = get_object_or_404(NewsAndEvents, pk=pk)
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST, request.FILES, instance=instance)
        title = request.POST.get("title")
        if form.is_valid():
            form.save()

            messages.success(request, (title + " ha sido actualizado exitosamente."))
            return redirect("home")
        else:
            messages.error(request, "Por favor corrige los errores a continuación.")
    else:
        form = NewsAndEventsForm(instance=instance)
    return render(
        request,
        "core/post_add.html",
        {
            "title": "Editar Publicación",
            "form": form,
        },
    )


@login_required
@lecturer_required
def delete_post(request, pk):
    post = get_object_or_404(NewsAndEvents, pk=pk)
    title = post.title
    post.delete()
    messages.success(request, (title + " ha sido eliminado exitosamente."))
    return redirect("home")


# ########################################################
# Session
# ########################################################
@login_required
@lecturer_required
def session_list_view(request):
    """Show list of all sessions"""
    sessions = Session.objects.all().order_by("-is_current_session", "-session")
    return render(request, "core/session_list.html", {"sessions": sessions})


@login_required
@lecturer_required
def session_add_view(request):
    """check request method, if POST we add session otherwise show empty form"""
    if request.method == "POST":
        form = SessionForm(request.POST)
        if form.is_valid():
            data = form.data.get(
                "is_current_session"
            )  # returns string of 'True' if the user selected Yes
            print(data)
            if data == "true":
                sessions = Session.objects.all()
                if sessions:
                    for session in sessions:
                        if session.is_current_session == True:
                            unset = Session.objects.filter(is_current_session=True).first()
                            if unset:
                                unset.is_current_session = False
                                unset.save()
                    form.save()
                else:
                    form.save()
            else:
                form.save()
            messages.success(request, "Sesión agregada exitosamente.")
            return redirect("session_list")

    else:
        form = SessionForm()
    return render(request, "core/session_update.html", {"form": form})


@login_required
@lecturer_required
def session_update_view(request, pk):
    session = Session.objects.get(pk=pk)
    if request.method == "POST":
        form = SessionForm(request.POST, instance=session)
        data = form.data.get("is_current_session")
        if data == "true":
            sessions = Session.objects.all()
            if sessions:
                for session in sessions:
                    if session.is_current_session == True:
                        unset = Session.objects.filter(is_current_session=True).first()
                        if unset:
                            unset.is_current_session = False
                            unset.save()

            if form.is_valid():
                form.save()
                messages.success(request, "Sesión actualizada exitosamente.")
                return redirect("session_list")
        else:
            form = SessionForm(request.POST, instance=session)
            if form.is_valid():
                form.save()
                messages.success(request, "Sesión actualizada exitosamente.")
                return redirect("session_list")

    else:
        form = SessionForm(instance=session)
    return render(request, "core/session_update.html", {"form": form})


@login_required
@lecturer_required
def session_delete_view(request, pk):
    session = get_object_or_404(Session, pk=pk)

    if session.is_current_session:
        messages.error(request, "No puedes eliminar la sesión actual")
        return redirect("session_list")
    else:
        session.delete()
        messages.success(request, "Sesión eliminada exitosamente")
    return redirect("session_list")


# ########################################################


# ########################################################
# Semester
# ########################################################
@login_required
@lecturer_required
def semester_list_view(request):
    semesters = Semester.objects.all().order_by("-is_current_semester", "-semester")
    return render(
        request,
        "core/semester_list.html",
        {
            "semesters": semesters,
        },
    )


@login_required
@lecturer_required
def semester_add_view(request):
    if request.method == "POST":
        form = SemesterForm(request.POST)
        if form.is_valid():
            data = form.data.get(
                "is_current_semester"
            )  # returns string of 'True' if the user selected Yes
            if data == "True":
                semester = form.data.get("semester")
                ss = form.data.get("session")
                session = Session.objects.get(pk=ss)
                try:
                    if Semester.objects.get(semester=semester, session=ss):
                        messages.error(
                            request,
                            "El semestre "
                            + semester
                            + " en la sesión "
                            + session.session
                            + " ya existe",
                        )
                        return redirect("add_semester")
                except:
                    semesters = Semester.objects.all()
                    sessions = Session.objects.all()
                    if semesters:
                        for semester in semesters:
                            if semester.is_current_semester == True:
                                unset_semester = Semester.objects.get(
                                    is_current_semester=True
                                )
                                unset_semester.is_current_semester = False
                                unset_semester.save()
                        for session in sessions:
                            if session.is_current_session == True:
                                unset_session = Session.objects.get(
                                    is_current_session=True
                                )
                                unset_session.is_current_session = False
                                unset_session.save()

                    new_session = request.POST.get("session")
                    set_session = Session.objects.get(pk=new_session)
                    set_session.is_current_session = True
                    set_session.save()
                    form.save()
                    messages.success(request, "Semestre agregado exitosamente.")
                    return redirect("semester_list")

            form.save()
            messages.success(request, "Semestre agregado exitosamente.")
            return redirect("semester_list")
    else:
        form = SemesterForm()
    return render(request, "core/semester_update.html", {"form": form})


@login_required
@lecturer_required
def semester_update_view(request, pk):
    semester = Semester.objects.get(pk=pk)
    if request.method == "POST":
        if (
            request.POST.get("is_current_semester") == "True"
        ):  # returns string of 'True' if the user selected yes for 'is current semester'
            unset_semester = Semester.objects.filter(is_current_semester=True).first()
            if unset_semester:
                unset_semester.is_current_semester = False
                unset_semester.save()
            unset_session = Session.objects.filter(is_current_session=True).first()
            if unset_session:
                unset_session.is_current_session = False
                unset_session.save()
            new_session = request.POST.get("session")
            form = SemesterForm(request.POST, instance=semester)
            if form.is_valid():
                set_session = Session.objects.get(pk=new_session)
                set_session.is_current_session = True
                set_session.save()
                form.save()
                messages.success(request, "Semestre actualizado exitosamente!")
                return redirect("semester_list")
        else:
            form = SemesterForm(request.POST, instance=semester)
            if form.is_valid():
                form.save()
                return redirect("semester_list")

    else:
        form = SemesterForm(instance=semester)
    return render(request, "core/semester_update.html", {"form": form})


@login_required
@lecturer_required
def semester_delete_view(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if semester.is_current_semester:
        messages.error(request, "No puedes eliminar el semestre actual")
        return redirect("semester_list")
    else:
        semester.delete()
        messages.success(request, "Semestre eliminado exitosamente")
    return redirect("semester_list")


# ########################################################
# Public Pages
# ########################################################
def public_home_view(request):
    """Página pública de inicio"""
    items = NewsAndEvents.objects.all().order_by("-updated_date")[:6]  # Solo mostrar 6 items más recientes
    context = {
        "title": "Inicio - Sistema de Gestión Académica",
        "items": items,
    }
    return render(request, "core/public_home.html", context)


def about_view(request):
    """Página pública sobre nosotros"""
    context = {
        "title": "Sobre Nosotros",
    }
    return render(request, "core/about.html", context)


def contact_view(request):
    """Página pública de contacto"""
    return render(request, "core/contact.html", {"title": "Contáctanos"})


def public_courses_view(request):
    """Vista para mostrar los cursos disponibles al público"""
    from course.models import Course, Program
    
    # Obtener todos los programas (sin filtro is_active ya que no existe)
    programs = Program.objects.all()
    courses = Course.objects.filter(is_active=True).select_related('program')
    
    context = {
        "title": "Nuestros Cursos",
        "programs": programs,
        "courses": courses,
    }
    return render(request, "core/public_courses.html", context)
