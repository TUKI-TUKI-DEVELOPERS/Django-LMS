from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus.tables import Table
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import simpleSplit
from io import BytesIO
from reportlab.lib.units import inch
from reportlab.lib import colors

from accounts.models import Student, DepartmentHead
from quiz.models import Sitting, Quiz, Progress
import re
from core.models import Session, Semester
from course.models import Course
from accounts.decorators import lecturer_required, student_required
from .models import TakenCourse, Result, FIRST, SECOND, Certificate
from django.template.loader import get_template
from xhtml2pdf import pisa


cm = 2.54


# ########################################################
# Department Head: Program Course Grades (Read-only)
# ########################################################
@login_required
def program_course_grades(request):
    """Vista para que el Jefe de Departamento vea calificaciones de cursos de su programa.

    - Jefe de departamento: ve cursos de su programa y las calificaciones de alumnos.
    - Admin/Staff: puede ver todos los programas/cursos.
    """
    # Verificación de permisos
    is_admin = request.user.is_superuser or request.user.is_staff
    if not (is_admin or getattr(request.user, 'is_dep_head', False)):
        messages.error(request, "No autorizado.")
        return redirect('home')

    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = None
    if current_session:
        current_semester = Semester.objects.filter(is_current_semester=True, session=current_session).first()

    # Determinar programa
    program = None
    if is_admin:
        # Admin puede filtrar por programa por querystring
        program_id = request.GET.get('program')
        if program_id:
            from course.models import Program
            program = Program.objects.filter(id=program_id).first()
    else:
        # Jefe de departamento: su programa asociado
        try:
            dep = DepartmentHead.objects.select_related('department').get(user=request.user)
            program = dep.department
        except DepartmentHead.DoesNotExist:
            messages.error(request, "No se encontró el programa del jefe de departamento.")
            return redirect('home')

    # Cursos del programa
    courses_qs = Course.objects.all()
    if program:
        courses_qs = courses_qs.filter(program=program)
    if current_semester:
        courses_qs = courses_qs.filter(semester=current_semester.semester)

    # Filtros opcionales
    course_id = request.GET.get('course')
    if course_id:
        courses_qs = courses_qs.filter(id=course_id)

    # Traer calificaciones de TakenCourse para esos cursos
    taken = TakenCourse.objects.filter(course__in=courses_qs).select_related('student__student', 'course')

    # Agrupar por curso
    from collections import defaultdict
    course_to_taken = defaultdict(list)
    for tc in taken:
        course_to_taken[tc.course].append(tc)

    context = {
        'program': program,
        'courses': list(courses_qs.order_by('title')),
        'course_to_taken': dict(course_to_taken),
        'current_session': current_session,
        'current_semester': current_semester,
        'selected_course_id': int(course_id) if course_id else None,
        'is_admin': is_admin,
    }
    return render(request, 'result/program_course_grades.html', context)

# ########################################################
# Score Add & Add for
# ########################################################
@login_required
@lecturer_required
def add_score(request):
    """
    Shows a page where a lecturer will select a course allocated
    to him for score entry. in a specific semester and session
    """
    current_session = Session.objects.filter(is_current_session=True).first()
    if not current_session:
        messages.error(request, "No hay una sesión activa configurada.")
        return render(request, "result/add_score.html")
    
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()

    if not current_semester:
        messages.error(request, "No hay un semestre activo configurado para esta sesión.")
        return render(request, "result/add_score.html")

    # semester = Course.objects.filter(
    # allocated_course__lecturer__pk=request.user.id,
    # semester=current_semester)
    courses = Course.objects.filter(
        allocated_course__lecturer__pk=request.user.id
    ).filter(semester=current_semester)
    
    if not courses.exists():
        messages.warning(request, "No hay cursos asignados para este semestre")
    
    # Handle POST request for course selection
    if request.method == "POST":
        course_id = request.POST.get('course')
        if course_id:
            return HttpResponseRedirect(reverse_lazy("add_score_for", kwargs={"id": course_id}))
        else:
            messages.error(request, "Por favor selecciona un curso.")
    
    context = {
        "current_session": current_session,
        "current_semester": current_semester,
        "courses": courses,
    }
    return render(request, "result/add_score.html", context)


@login_required
@lecturer_required
def add_score_for(request, id):
    """
    Shows a page where a lecturer will add score for students that
    are taking courses allocated to him in a specific semester and session
    """
    current_session = Session.objects.filter(is_current_session=True).first()
    if not current_session:
        messages.error(request, "No hay una sesión activa configurada.")
        return render(request, "result/add_score_for.html", {"error": "No hay sesión activa"})
    
    current_semester = get_object_or_404(
        Semester, is_current_semester=True, session=current_session
    )
    if request.method == "GET":
        courses = Course.objects.filter(
            allocated_course__lecturer__pk=request.user.id
        ).filter(semester=current_semester)
        course = Course.objects.get(pk=id)
        
        # Verificar que el profesor esté asignado a este curso
        if not course.allocated_course.filter(lecturer__pk=request.user.id).exists():
            messages.error(request, "No tienes permisos para gestionar este curso.")
            return redirect("add_score")
        
        # Buscar estudiantes que están tomando este curso específico
        # y que el curso esté asignado al profesor actual
        students = TakenCourse.objects.filter(
            course__id=id,
            course__allocated_course__lecturer__pk=request.user.id
        ).select_related('student', 'course')
        
        # Verificar todos los TakenCourse para este curso (sin filtros)
        all_taken_courses = TakenCourse.objects.filter(course__id=id)
        
        if not students.exists():
            messages.warning(request, f"No se encontraron estudiantes para el curso '{course.title}'")
        
        # ----------------------------------------------
        # Autocompletar promedios desde exámenes (assignment/exam/practice)
        # ----------------------------------------------
        # Mapear quizzes del curso por título y categoría (con heurística por título si no hay categoría)
        course_quizzes = Quiz.objects.filter(course=course).only('id', 'title', 'category')

        def resolve_category(quiz_obj):
            """Devuelve 'assignment' | 'exam' | 'practice' o None.
            Prioriza el campo category; si viene vacío/none/'none', infiere por el título (ES/EN).
            """
            raw = (getattr(quiz_obj, 'category', '') or '').strip().lower()
            if raw in ('assignment', 'exam', 'practice'):
                return raw
            if not raw or raw == 'none':
                title_l = (getattr(quiz_obj, 'title', '') or '').strip().lower()
                # Assignment / Tarea
                if any(k in title_l for k in ['assignment', 'tarea', 'tareas']):
                    return 'assignment'
                # Practice / Quiz / Cuestionario / Práctica
                if any(k in title_l for k in ['practice', 'práctica', 'practica', 'quiz', 'cuestionario']):
                    return 'practice'
                # Exam / Examen / Parcial / Final / Mid
                if any(k in title_l for k in ['exam', 'examen', 'parcial', 'final', 'mid']):
                    return 'exam'
            return None

        title_to_category = {q.title: resolve_category(q) for q in course_quizzes}

        # Función de ayuda para parsear Progress.score → [(title, score, possible)]
        def parse_progress_entries(score_blob):
            if not score_blob:
                return []
            entries = []
            # Coincide segmentos: <titulo>,<score>,<possible>,
            pattern = re.compile(r"([^,]+),(\d+),(\d+),")
            for match in pattern.finditer(score_blob):
                title = match.group(1).strip()
                score = int(match.group(2))
                possible = int(match.group(3)) or 1
                entries.append((title, score, possible))
            return entries

        # Calcular promedios por estudiante
        for tc in students:
            user = tc.student.student  # User object

            # 1) Intentar con Sittings completados (preferido)
            sittings = (
                Sitting.objects.filter(user=user, course=course, complete=True)
                .select_related('quiz')
            )
            cat_to_percents = {'assignment': [], 'exam': [], 'practice': []}
            exam_mid_percents: list[float] = []
            exam_final_percents: list[float] = []
            for s in sittings:
                category = resolve_category(s.quiz)
                if category in cat_to_percents:
                    try:
                        percent = s.get_percent_correct
                    except Exception:
                        # fallback si no se puede computar porcentaje
                        max_score = s.get_max_score if hasattr(s, 'get_max_score') else 0
                        percent = (float(s.current_score) / max_score * 100) if max_score else 0
                    cat_to_percents[category].append(percent)
                    if category == 'exam':
                        title_l = (s.quiz.title or '').lower()
                        if any(x in title_l for x in ['final']):
                            exam_final_percents.append(percent)
                        elif any(x in title_l for x in ['parcial', 'partial', 'mid']):
                            exam_mid_percents.append(percent)
                        else:
                            # Si no se puede clasificar, asumir parcial
                            exam_mid_percents.append(percent)

            # 2) Fallback con Progress si faltan categorías
            need_fallback = any(len(v) == 0 for v in cat_to_percents.values())
            if need_fallback:
                prog = Progress.objects.filter(user=user).first()
                if prog and prog.score:
                    for title, sc, poss in parse_progress_entries(prog.score):
                        # Resolver categoría por título si falta
                        cat = title_to_category.get(title)
                        if cat is None:
                            title_l = (title or '').lower()
                            if any(k in title_l for k in ['assignment', 'tarea', 'tareas']):
                                cat = 'assignment'
                            elif any(k in title_l for k in ['practice', 'práctica', 'practica', 'quiz', 'cuestionario']):
                                cat = 'practice'
                            elif any(k in title_l for k in ['exam', 'examen', 'parcial', 'final', 'mid']):
                                cat = 'exam'
                        if cat in cat_to_percents and len(cat_to_percents[cat]) == 0:
                            cat_to_percents[cat].append((sc / poss) * 100.0)
                        # Clasificar exámenes por nombre si aplica
                        if cat == 'exam':
                            title_l = (title or '').lower()
                            val = (sc / poss) * 100.0
                            if any(x in title_l for x in ['final']):
                                if len(exam_final_percents) == 0:
                                    exam_final_percents.append(val)
                            elif any(x in title_l for x in ['parcial', 'partial', 'mid']):
                                if len(exam_mid_percents) == 0:
                                    exam_mid_percents.append(val)
                            else:
                                if len(exam_mid_percents) == 0:
                                    exam_mid_percents.append(val)

            # Calcular asistencia como % de quizzes completados del curso
            try:
                total_quizzes_count = course_quizzes.count()
                completed_quiz_ids = set(sittings.values_list('quiz_id', flat=True))
                attendance_percent = round((len(completed_quiz_ids) / total_quizzes_count) * 100, 2) if total_quizzes_count else 0.0
            except Exception:
                attendance_percent = 0.0

            # 3) Calcular promedios (redondeados a 2 decimales)
            def avg_or_zero(values):
                return round(sum(values) / len(values), 2) if values else 0.0

            assignment_avg = avg_or_zero(cat_to_percents['assignment'])
            # exam: separar en parcial/final por heurística del título
            exam_mid_avg = avg_or_zero(exam_mid_percents)
            exam_final_avg = avg_or_zero(exam_final_percents)
            practice_avg = avg_or_zero(cat_to_percents['practice'])

            # 4) Prefijar en los objetos (solo si están en cero)
            try:
                if not tc.assignment or float(tc.assignment) == 0.0:
                    tc.assignment = assignment_avg
                if not tc.mid_exam or float(tc.mid_exam) == 0.0:
                    tc.mid_exam = exam_mid_avg
                if not tc.quiz or float(tc.quiz) == 0.0:
                    tc.quiz = practice_avg
                if not tc.attendance or float(tc.attendance) == 0.0:
                    tc.attendance = attendance_percent
                if not tc.final_exam or float(tc.final_exam) == 0.0:
                    tc.final_exam = exam_final_avg
            except Exception:
                # Ignorar problemas de conversión y continuar
                pass

        context = {
            "title": "Submit Score",
            "courses": courses,
            "course": course,
            "students": students,
            "current_session": current_session,
            "current_semester": current_semester,
        }
        return render(request, "result/add_score_for.html", context)

    if request.method == "POST":
        data = request.POST.copy()
        data.pop("csrfmiddlewaretoken", None)  # remove csrf_token
        
        # Get all student IDs from the form data
        student_ids = set()
        for key in data.keys():
            if key.startswith('assignment_'):
                student_id = key.replace('assignment_', '')
                student_ids.add(student_id)
        
        for student_id in student_ids:
            try:
                # Get the student's TakenCourse object
                student_taken_course = TakenCourse.objects.get(
                    course__id=id,
                    student__student__id=student_id,
                    course__allocated_course__lecturer__pk=request.user.id
                )
                
                # Function to round scores automatically
                def round_score(score_str):
                    """Convert score to float and round to nearest integer if it has decimals"""
                    if not score_str:
                        return ''
                    try:
                        score_float = float(score_str)
                        # Round to nearest integer
                        return str(round(score_float))
                    except (ValueError, TypeError):
                        return ''
                
                # Get scores for this student and round them
                assignment = round_score(data.get(f'assignment_{student_id}', ''))
                mid_exam = round_score(data.get(f'mid_exam_{student_id}', ''))
                quiz = round_score(data.get(f'quiz_{student_id}', ''))
                attendance = round_score(data.get(f'attendance_{student_id}', ''))
                final_exam = round_score(data.get(f'final_exam_{student_id}', ''))
                
                # Only update if at least one score is provided
                if any([assignment, mid_exam, quiz, attendance, final_exam]):
                    # Update the TakenCourse object with rounded scores
                    if assignment:
                        student_taken_course.assignment = assignment
                    if mid_exam:
                        student_taken_course.mid_exam = mid_exam
                    if quiz:
                        student_taken_course.quiz = quiz
                    if attendance:
                        student_taken_course.attendance = attendance
                    if final_exam:
                        student_taken_course.final_exam = final_exam
                    
                    # Calculate weighted total (Assignment 20%, Mid 25%, Quiz 15%, Attendance 10%, Final 30%)
                    def to_float(val):
                        try:
                            return float(val)
                        except Exception:
                            return 0.0
                    a = to_float(assignment)
                    m = to_float(mid_exam)
                    q = to_float(quiz)
                    att = to_float(attendance)
                    f = to_float(final_exam)
                    total = round(a * 0.20 + m * 0.25 + q * 0.15 + att * 0.10 + f * 0.30, 2)
                    student_taken_course.total = total
                    
                    # Calculate grade based on total
                    if total >= 80:
                        student_taken_course.grade = 'A'
                    elif total >= 70:
                        student_taken_course.grade = 'B'
                    elif total >= 60:
                        student_taken_course.grade = 'C'
                    elif total >= 50:
                        student_taken_course.grade = 'D'
                    else:
                        student_taken_course.grade = 'F'
                    
                    # Set comment
                    student_taken_course.comment = 'PASS' if total >= 50 else 'FAIL'

                    # Calculate points (credit * weight by grade)
                    try:
                        student_taken_course.point = student_taken_course.get_point(student_taken_course.grade)
                    except Exception:
                        pass
                    
                    student_taken_course.save()

                    # Emitir/actualizar certificado si el estudiante aprobó
                    if student_taken_course.comment == 'PASS':
                        cert, created = Certificate.objects.get_or_create(
                            taken_course=student_taken_course,
                            defaults={
                                'serial_number': Certificate.generate_serial(),
                                'issued_by': request.user,
                            }
                        )
                        if not created and cert.issued_by is None:
                            cert.issued_by = request.user
                            cert.save(update_fields=['issued_by'])
                    # Check if any rounding occurred
                    original_scores = [
                        data.get(f'assignment_{student_id}', ''),
                        data.get(f'mid_exam_{student_id}', ''),
                        data.get(f'quiz_{student_id}', ''),
                        data.get(f'attendance_{student_id}', ''),
                        data.get(f'final_exam_{student_id}', '')
                    ]
                    rounded_scores = [assignment, mid_exam, quiz, attendance, final_exam]
                    
                    # Check if any score was rounded
                    was_rounded = False
                    for orig, rounded in zip(original_scores, rounded_scores):
                        if orig and rounded and str(orig) != str(rounded):
                            was_rounded = True
                            break
                    
                    if was_rounded:
                        messages.success(request, f"Calificaciones actualizadas para {student_taken_course.student.student.get_full_name} (valores decimales redondeados automáticamente)")
                    else:
                        messages.success(request, f"Calificaciones actualizadas para {student_taken_course.student.student.get_full_name}")
                else:
                    messages.warning(request, f"No se proporcionaron calificaciones para {student_taken_course.student.student.get_full_name}")
                    
            except TakenCourse.DoesNotExist:
                messages.error(request, f"No se encontró el registro del estudiante con ID {student_id}")
            except Exception as e:
                messages.error(request, f"Error al actualizar calificaciones: {str(e)}")
        
        return redirect("add_score_for", id=id)


# ########################################################


@login_required
@student_required
def grade_result(request):
    student = Student.objects.get(student__pk=request.user.id)
    # Mostrar todos los cursos tomados por el estudiante, sin filtrar por level
    # (evita inconsistencias si el valor almacenado de level está traducido)
    courses = TakenCourse.objects.filter(student__student__pk=request.user.id)
    # total_credit_in_semester = 0
    # Si existen resultados agregados por semestre (Result), se muestran; si no, la tabla de cursos seguirá visible
    results = Result.objects.filter(student__student__pk=request.user.id)

    result_set = set()

    for result in results:
        result_set.add(result.session)

    sorted_result = sorted(result_set)

    # Normalizar semestre (soporta traducciones: "Primer", "Segundo")
    def normalize_semester(value: str) -> str:
        s = (str(value) if value is not None else "").lower()
        if any(k in s for k in ["first", "primer", "primero", "1"]):
            return "First"
        if any(k in s for k in ["second", "segun", "segundo", "2"]):
            return "Second"
        return "Other"

    courses_first = [c for c in courses if normalize_semester(c.course.semester) == "First"]
    courses_second = [c for c in courses if normalize_semester(c.course.semester) == "Second"]

    total_first_semester_credit = sum(int(c.course.credit) for c in courses_first)
    total_sec_semester_credit = sum(int(c.course.credit) for c in courses_second)

    previousCGPA = 0
    # previousLEVEL = 0
    # calculate_cgpa
    for i in results:
        previousLEVEL = i.level
        try:
            a = Result.objects.get(
                student__student__pk=request.user.id,
                level=previousLEVEL,
                semester="Second",
            )
            previousCGPA = a.cgpa
            break
        except:
            previousCGPA = 0

    context = {
        "courses": courses,
        "courses_first": courses_first,
        "courses_second": courses_second,
        "results": results,
        "sorted_result": sorted_result,
        "student": student,
        "total_first_semester_credit": total_first_semester_credit,
        "total_sec_semester_credit": total_sec_semester_credit,
        "total_first_and_second_semester_credit": total_first_semester_credit
        + total_sec_semester_credit,
        "previousCGPA": previousCGPA,
    }

    return render(request, "result/grade_results.html", context)


@login_required
@student_required
def assessment_result(request):
    student = Student.objects.get(student__pk=request.user.id)
    # No filtrar por level para evitar mismatch entre 'Bachelor' y 'Bachelor Degree'
    courses = TakenCourse.objects.filter(
        student__student__pk=request.user.id
    )
    result = Result.objects.filter(student__student__pk=request.user.id)

    # Normalizar semestre para agrupar
    def normalize_semester(value: str) -> str:
        s = (str(value) if value is not None else "").lower()
        if any(k in s for k in ["first", "primer", "primero", "1"]):
            return "First"
        if any(k in s for k in ["second", "segun", "segundo", "2"]):
            return "Second"
        return "Other"

    courses_first = [c for c in courses if normalize_semester(c.course.semester) == "First"]
    courses_second = [c for c in courses if normalize_semester(c.course.semester) == "Second"]

    context = {
        "courses": courses,
        "courses_first": courses_first,
        "courses_second": courses_second,
        "result": result,
        "student": student,
    }

    return render(request, "result/assessment_results.html", context)


@login_required
@lecturer_required
def result_sheet_pdf_view(request, id):
    current_semester = Semester.objects.filter(is_current_semester=True).first()
    if not current_semester:
        messages.error(request, "No hay un semestre activo configurado.")
        return HttpResponse("No hay semestre activo configurado", status=400)
    
    current_session = Session.objects.filter(is_current_session=True).first()
    if not current_session:
        messages.error(request, "No hay una sesión activa configurada.")
        return HttpResponse("No hay sesión activa configurada", status=400)
    result = TakenCourse.objects.filter(course__pk=id)
    course = get_object_or_404(Course, id=id)
    no_of_pass = TakenCourse.objects.filter(course__pk=id, comment="PASS").count()
    no_of_fail = TakenCourse.objects.filter(course__pk=id, comment="FAIL").count()
    fname = (
        str(current_semester)
        + "_semester_"
        + str(current_session)
        + "_"
        + str(course)
        + "_resultSheet.pdf"
    )
    fname = fname.replace("/", "-")
    flocation = settings.MEDIA_ROOT + "/result_sheet/" + fname

    doc = SimpleDocTemplate(
        flocation,
        rightMargin=0,
        leftMargin=6.5 * cm,
        topMargin=0.3 * cm,
        bottomMargin=0,
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(name="ParagraphTitle", fontSize=11, fontName="FreeSansBold")
    )
    Story = [Spacer(1, 0.2)]
    style = styles["Normal"]

    # picture = request.user.picture
    # l_pic = Image(picture, 1*inch, 1*inch)
    # l_pic.__setattr__("_offs_x", 200)
    # l_pic.__setattr__("_offs_y", -130)
    # Story.append(l_pic)

    # logo = settings.MEDIA_ROOT + "/logo/logo-mini.png"
    # im_logo = Image(logo, 1*inch, 1*inch)
    # im_logo.__setattr__("_offs_x", -218)
    # im_logo.__setattr__("_offs_y", -60)
    # Story.append(im_logo)

    print("\nsettings.MEDIA_ROOT", settings.MEDIA_ROOT)
    print("\nsettings.STATICFILES_DIRS[0]", settings.STATICFILES_DIRS[0])
    logo = settings.STATICFILES_DIRS[0] + "/img/dj-lms.png"
    im = Image(logo, 1 * inch, 1 * inch)
    im.__setattr__("_offs_x", -200)
    im.__setattr__("_offs_y", -45)
    Story.append(im)

    style = getSampleStyleSheet()
    normal = style["Normal"]
    normal.alignment = TA_CENTER
    normal.fontName = "Helvetica"
    normal.fontSize = 12
    normal.leading = 15
    title = (
        "<b> "
        + str(current_semester)
        + " Semester "
        + str(current_session)
        + " Result Sheet</b>"
    )
    title = Paragraph(title.upper(), normal)
    Story.append(title)
    Story.append(Spacer(1, 0.1 * inch))

    style = getSampleStyleSheet()
    normal = style["Normal"]
    normal.alignment = TA_CENTER
    normal.fontName = "Helvetica"
    normal.fontSize = 10
    normal.leading = 15
    title = "<b>Course lecturer: " + request.user.get_full_name + "</b>"
    title = Paragraph(title.upper(), normal)
    Story.append(title)
    Story.append(Spacer(1, 0.1 * inch))

    normal = style["Normal"]
    normal.alignment = TA_CENTER
    normal.fontName = "Helvetica"
    normal.fontSize = 10
    normal.leading = 15
    level = result.filter(course_id=id).first()
    title = "<b>Level: </b>" + str(level.course.level)
    title = Paragraph(title.upper(), normal)
    Story.append(title)
    Story.append(Spacer(1, 0.6 * inch))

    elements = []
    count = 0
    header = [("S/N", "ID NO.", "FULL NAME", "TOTAL", "GRADE", "POINT", "COMMENT")]

    table_header = Table(header, [inch], [0.5 * inch])
    table_header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.black),
                ("TEXTCOLOR", (1, 0), (-1, -1), colors.white),
                ("TEXTCOLOR", (0, 0), (0, 0), colors.cyan),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    Story.append(table_header)

    for student in result:
        data = [
            (
                count + 1,
                student.student.student.username.upper(),
                Paragraph(
                    student.student.student.get_full_name.capitalize(), styles["Normal"]
                ),
                student.total,
                student.grade,
                student.point,
                student.comment,
            )
        ]
        color = colors.black
        if student.grade == "F":
            color = colors.red
        count += 1

        t_body = Table(data, colWidths=[inch])
        t_body.setStyle(
            TableStyle(
                [
                    ("INNERGRID", (0, 0), (-1, -1), 0.05, colors.black),
                    ("BOX", (0, 0), (-1, -1), 0.1, colors.black),
                ]
            )
        )
        Story.append(t_body)

    Story.append(Spacer(1, 1 * inch))
    style_right = ParagraphStyle(
        name="right", parent=styles["Normal"], alignment=TA_RIGHT
    )
    tbl_data = [
        [
            Paragraph("<b>Date:</b>_____________________________", styles["Normal"]),
            Paragraph("<b>No. of PASS:</b> " + str(no_of_pass), style_right),
        ],
        [
            Paragraph(
                "<b>Siganture / Stamp:</b> _____________________________",
                styles["Normal"],
            ),
            Paragraph("<b>No. of FAIL: </b>" + str(no_of_fail), style_right),
        ],
    ]
    tbl = Table(tbl_data)
    Story.append(tbl)

    doc.build(Story)

    fs = FileSystemStorage(settings.MEDIA_ROOT + "/result_sheet")
    with fs.open(fname) as pdf:
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = "inline; filename=" + fname + ""
        return response
    return response


# ########################################################
# Certificates
# ########################################################

@login_required
def certificate_list(request):
    """Lista de certificados del usuario actual (estudiante o profesor)."""
    if request.user.is_student:
        student = Student.objects.get(student__pk=request.user.id)
        passed = TakenCourse.objects.filter(student=student, comment="PASS").select_related('course', 'student')
    elif request.user.is_lecturer:
        # Profesores: ver certificados de sus cursos aprobados por alumnos (resumen)
        passed = TakenCourse.objects.filter(
            course__allocated_course__lecturer__pk=request.user.id, comment="PASS"
        ).select_related('student', 'course')
    else:
        passed = TakenCourse.objects.none()

    # Autoemitir certificados faltantes para aprobados (política: emisión automática en PASS)
    for tc in passed:
        if not Certificate.objects.filter(taken_course=tc).exists():
            Certificate.objects.get_or_create(
                taken_course=tc,
                defaults={
                    'serial_number': Certificate.generate_serial(),
                    'issued_by': request.user if (request.user.is_superuser or request.user.is_lecturer) else None,
                }
            )

    passed = passed.select_related('course', 'student', 'certificate') if hasattr(passed, 'select_related') else passed
    return render(request, "result/certificate_list.html", {"passed": passed})


@login_required
def certificate_pdf_view(request, id):
    """Genera PDF de certificado para un TakenCourse aprobado (ReportLab)."""
    tc = get_object_or_404(TakenCourse, id=id)
    # Autorización básica: estudiante dueño o profesor del curso o admin
    if not (
        request.user.is_superuser
        or (request.user.is_student and tc.student.student_id == request.user.id)
        or (
            request.user.is_lecturer
            and tc.course.allocated_course.filter(lecturer__pk=request.user.id).exists()
        )
    ):
        messages.error(request, "No estás autorizado para ver este certificado.")
        return redirect("home")

    if tc.comment != "PASS":
        messages.error(request, "El estudiante no está aprobado en este curso.")
        return redirect("certificate_list")

    cert = Certificate.objects.filter(taken_course=tc).first()
    if cert and cert.status == Certificate.STATUS_SUSPENDED and not request.user.is_superuser:
        messages.error(request, "Este certificado está suspendido.")
        return redirect("certificate_list")
    # Autoemitir si no existe certificado
    if cert is None:
        cert = Certificate.objects.create(
            taken_course=tc,
            serial_number=Certificate.generate_serial(),
            issued_by=request.user if (request.user.is_superuser or request.user.is_lecturer) else None,
        )

    # Recursos
    try:
        logo_path = settings.STATICFILES_DIRS[0] + "/img/logo-aprendeya.png"
    except Exception:
        logo_path = None
    company_name = "Aprende Ya"
    company_city = "Santiago, Chile"
    company_website = "https://aprendeyacapacitacion.cl"

    # Duración del curso (opcional)
    try:
        duration_value = getattr(tc.course, "duration", None)
        duration_unit = getattr(tc.course, "duration_unit", None)
        unit_display = tc.course.get_duration_unit_display() if hasattr(tc.course, "get_duration_unit_display") and duration_unit else None
        if duration_value and unit_display:
            course_duration_text = f"{duration_value} {unit_display}"
        elif duration_value:
            course_duration_text = f"{duration_value} horas"
        else:
            course_duration_text = "110 horas totales (102 teóricas y 8 prácticas)"
    except Exception:
        course_duration_text = "110 horas totales (102 teóricas y 8 prácticas)"

    # Render PDF en memoria
    buffer = BytesIO()
    from reportlab.lib.pagesizes import A4, landscape
    width, height = landscape(A4)  # Horizontal
    c = rl_canvas.Canvas(buffer, pagesize=A4)
    c.setPageSize((width, height))

    margin = 40
    header_h = 86
    # Paleta corporativa
    dark_gray = (69/255.0, 69/255.0, 69/255.0)
    lime = (146/255.0, 182/255.0, 42/255.0)
    navy = (32/255.0, 32/255.0, 68/255.0)
    dark_red = (159/255.0, 8/255.0, 31/255.0)
    mustard = (226/255.0, 210/255.0, 41/255.0)

    # Fondo con imagen (si existe)
    try:
        bg_path = settings.STATICFILES_DIRS[0] + "/img/pic-8.png"
        c.drawImage(bg_path, 0, 0, width=width, height=height, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    # Panel blanco solo en el lado derecho para legibilidad (deja visible el fondo a la izquierda)
    panel_left = width * 0.40
    panel_width = width - panel_left - margin
    c.setFillColorRGB(1, 1, 1)
    c.rect(panel_left, margin, panel_width, height - 2 * margin, fill=1, stroke=0)

    # Logo en cabecera (izquierda)
    if logo_path:
        try:
            lw, lh = 160, 72  # logo más grande
            lx = margin
            ly = height - margin - lh - 8
            c.drawImage(logo_path, lx, ly, width=lw, height=lh, preserveAspectRatio=True, mask='auto')
            # Enlace clicable al sitio
            c.linkURL(company_website, (lx, ly, lx + lw, ly + lh), relative=0)
        except Exception:
            pass

    # Título en cabecera (derecha) sobre fondo blanco
    c.setFillColorRGB(*dark_gray)
    c.setFont("Helvetica-Bold", 30)
    c.drawRightString(width - margin - 10, height - margin - 36, "CERTIFICADO")
    c.setFont("Helvetica", 12)
    c.drawRightString(width - margin - 10, height - margin - 56, "Otorgado al participante")

    # Acentos superiores (lima + mostaza) alineados al panel
    c.setFillColorRGB(*lime)
    c.rect(panel_left, height - margin - header_h + 4, panel_width, 6, fill=1, stroke=0)
    c.setFillColorRGB(*mustard)
    c.rect(panel_left, height - margin - header_h - 4, panel_width * 0.6, 3, fill=1, stroke=0)

    # Barra vertical lima derecha sutil
    c.setFillColorRGB(*lime)
    c.rect(width - margin - 10, margin, 10, height - 2 * margin - 60, fill=1, stroke=0)

    # Contenido
    # Contenido invertido a la derecha
    y = height - margin - header_h - 30
    right_x = width - margin - 18
    c.setFillColorRGB(*dark_gray)
    c.setFont("Helvetica", 12)
    c.drawRightString(right_x, y, "Se certifica que")
    y -= 20
    c.setFont("Helvetica-Bold", 22)
    c.setFillColorRGB(*dark_gray)
    c.drawRightString(right_x, y, tc.student.student.get_full_name)
    y -= 16
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.38, 0.38, 0.38)
    c.drawRightString(right_x, y, f"ID: {tc.student.student.username}")
    y -= 20
    c.setFillColorRGB(*dark_gray)
    c.setFont("Helvetica", 12)
    c.drawRightString(right_x, y, "ha sido capacitado(a), evaluado(a) y aprobado(a) en la actividad de")
    y -= 20
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(navy[0], navy[1], navy[2])
    c.drawRightString(right_x, y, f"{tc.course.title} ({tc.course.code})")
    y -= 18
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.26, 0.26, 0.26)
    c.drawRightString(right_x, y, f"Resultado final: {tc.total} ({tc.comment}) • Sede: Santiago, Chile")
    y -= 22
    # Párrafo adicional: narrativa corporativa + duración
    c.setFont("Helvetica", 11)
    c.setFillColorRGB(*dark_gray)
    paragraph_lines = [
        f"{company_name} certifica que el participante mencionado ha sido capacitado, evaluado y aprobado en la actividad de capacitación.",
        f"Componente formativo: {course_duration_text}.",
        f"Lugar de emisión: {company_city}.",
    ]
    max_width = width - 2*margin - 40
    for text in paragraph_lines:
        # Ajustar a ancho y alinear a la derecha
        wrapped = simpleSplit(text, "Helvetica", 11, max_width)
        for line in wrapped:
            c.drawRightString(right_x, y, line)
            y -= 14

    # Firma y serie
    c.setFont("Helvetica", 10)
    # Bloque firma (izquierda)
    c.setFillColorRGB(0, 0, 0)
    # Firma en el centro inferior
    c.line(width/2 - 120, margin + 40, width/2 + 120, margin + 40)
    c.drawCentredString(width/2, margin + 28, "Firma Autorizada")
    c.drawCentredString(width/2, margin + 16, "Camila Hernández")
    c.drawCentredString(width/2, margin + 4, "8.335.040-7")

    # Serie (derecha)
    c.setFillColorRGB(0.38, 0.38, 0.38)
    if cert:
        c.drawString(margin, margin + 28, f"N° Serie: {cert.serial_number}")
        c.drawString(margin, margin + 14, f"Emitido: {cert.issued_at.strftime('%d/%m/%Y')}")
    else:
        from django.utils.timezone import now
        c.drawString(margin, margin + 14, f"Emitido: {now().strftime('%d/%m/%Y')}")

    c.showPage()
    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=certificate_{tc.id}.pdf'
    return response


@login_required
def certificate_admin_list(request):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No autorizado.")
        return redirect('home')

    passed = TakenCourse.objects.filter(comment='PASS').select_related('course', 'student')
    return render(request, "result/certificate_admin_list.html", {"passed": passed})


@login_required
def certificate_admin_detail(request, id):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "No autorizado.")
        return redirect('home')

    tc = get_object_or_404(TakenCourse, id=id)
    cert = Certificate.objects.filter(taken_course=tc).first()
    if request.method == 'POST':
        if not (request.user.is_superuser or request.user.is_staff):
            messages.error(request, "No autorizado.")
            return redirect('certificate_admin_detail', id=id)
        action = request.POST.get('action')
        if action == 'suspend' and cert:
            cert.status = Certificate.STATUS_SUSPENDED
            cert.save(update_fields=['status'])
            messages.success(request, 'Certificado suspendido correctamente.')
        elif action == 'activate' and cert:
            cert.status = Certificate.STATUS_ACTIVE
            cert.save(update_fields=['status'])
            messages.success(request, 'Certificado activado correctamente.')
        return redirect('certificate_admin_detail', id=id)

    return render(request, "result/certificate_admin_detail.html", {"tc": tc, "cert": cert})


@login_required
def certificate_manage(request):
    """Gestión avanzada de certificados con filtros por curso y búsqueda de alumno.

    - Admin: ve todos los cursos y alumnos aprobados.
    - Profesor: ve solo cursos asignados y sus alumnos aprobados.
    """
    if request.user.is_superuser or request.user.is_staff or getattr(request.user, 'is_dep_head', False):
        courses = Course.objects.all().order_by('title')
        queryset = TakenCourse.objects.filter(comment='PASS').select_related('student', 'course')
    elif request.user.is_lecturer:
        courses = Course.objects.filter(allocated_course__lecturer__pk=request.user.id).order_by('title')
        queryset = TakenCourse.objects.filter(
            course__allocated_course__lecturer__pk=request.user.id,
            comment='PASS',
        ).select_related('student', 'course')
    else:
        messages.error(request, "No autorizado.")
        return redirect('home')

    course_id = request.GET.get('course')
    q = request.GET.get('q', '').strip()

    if course_id:
        queryset = queryset.filter(course__id=course_id)
    if q:
        queryset = queryset.filter(
            student__student__first_name__icontains=q
        ) | queryset.filter(
            student__student__last_name__icontains=q
        ) | queryset.filter(
            student__student__username__icontains=q
        )

    # Paginación simple opcional (no esencial)
    context = {
        'courses': courses,
        'certs': queryset.order_by('course__title', 'student__student__last_name'),
        'selected_course_id': int(course_id) if course_id else None,
        'q': q,
        'is_admin': request.user.is_superuser or request.user.is_staff or getattr(request.user, 'is_dep_head', False),
    }
    return render(request, 'result/certificate_manage.html', context)


@login_required
def certificate_generate(request, id):
    """Genera (o regenera) un certificado para un TakenCourse en PASS."""
    tc = get_object_or_404(TakenCourse, id=id)
    # Permisos: admin/staff o profesor del curso
    if not (
        request.user.is_superuser or request.user.is_staff or getattr(request.user, 'is_dep_head', False) or
        (request.user.is_lecturer and tc.course.allocated_course.filter(lecturer__pk=request.user.id).exists())
    ):
        messages.error(request, 'No autorizado.')
        return redirect('certificate_manage')

    if tc.comment != 'PASS':
        messages.error(request, 'El alumno no está aprobado en este curso.')
        return redirect('certificate_manage')

    cert, created = Certificate.objects.get_or_create(
        taken_course=tc,
        defaults={
            'serial_number': Certificate.generate_serial(),
            'issued_by': request.user,
        }
    )
    if not created:
        cert.serial_number = Certificate.generate_serial()
        cert.issued_by = request.user
        cert.save()

    messages.success(request, 'Certificado generado correctamente.')
    return redirect('certificate_manage')


@login_required
def certificate_bulk_generate(request):
    """Generación masiva para el filtro actual (solo admin/profesor)."""
    if request.method != 'POST':
        return redirect('certificate_manage')

    if request.user.is_superuser or request.user.is_staff or getattr(request.user, 'is_dep_head', False):
        queryset = TakenCourse.objects.filter(comment='PASS')
    elif request.user.is_lecturer:
        queryset = TakenCourse.objects.filter(
            course__allocated_course__lecturer__pk=request.user.id,
            comment='PASS',
        )
    else:
        messages.error(request, 'No autorizado.')
        return redirect('home')

    course_id = request.POST.get('course')
    q = request.POST.get('q', '').strip()
    if course_id:
        queryset = queryset.filter(course__id=course_id)
    if q:
        queryset = queryset.filter(
            student__student__first_name__icontains=q
        ) | queryset.filter(
            student__student__last_name__icontains=q
        ) | queryset.filter(
            student__student__username__icontains=q
        )

    generated = 0
    for tc in queryset.select_related('course', 'student'):
        cert, created = Certificate.objects.get_or_create(
            taken_course=tc,
            defaults={
                'serial_number': Certificate.generate_serial(),
                'issued_by': request.user,
            }
        )
        if not created:
            cert.serial_number = Certificate.generate_serial()
            cert.issued_by = request.user
            cert.save()
        generated += 1

    messages.success(request, f'Se generaron {generated} certificados.')
    return redirect('certificate_manage')


@login_required
def certificate_toggle_status(request, id):
    """Alterna ACTIVE/SUSPENDED de un certificado existente (admin/profesor)."""
    tc = get_object_or_404(TakenCourse, id=id)
    if not (
        request.user.is_superuser or request.user.is_staff or getattr(request.user, 'is_dep_head', False) or
        (request.user.is_lecturer and tc.course.allocated_course.filter(lecturer__pk=request.user.id).exists())
    ):
        messages.error(request, 'No autorizado.')
        return redirect('certificate_manage')

    cert = Certificate.objects.filter(taken_course=tc).first()
    if not cert:
        messages.error(request, 'No existe certificado para alternar estado.')
        return redirect('certificate_manage')

    cert.status = Certificate.STATUS_ACTIVE if cert.status == Certificate.STATUS_SUSPENDED else Certificate.STATUS_SUSPENDED
    cert.save(update_fields=['status'])
    messages.success(request, f'Certificado ahora está {cert.status}.')
    return redirect('certificate_manage')


@login_required
@student_required
def course_registration_form(request):
    current_semester = Semester.objects.filter(is_current_semester=True).first()
    if not current_semester:
        messages.error(request, "No hay un semestre activo configurado.")
        return HttpResponse("No hay semestre activo configurado", status=400)
    
    current_session = Session.objects.filter(is_current_session=True).first()
    if not current_session:
        messages.error(request, "No hay una sesión activa configurada.")
        return HttpResponse("No hay sesión activa configurada", status=400)
    courses = TakenCourse.objects.filter(student__student__id=request.user.id)
    fname = request.user.username + ".pdf"
    fname = fname.replace("/", "-")
    # flocation = '/tmp/' + fname
    # print(MEDIA_ROOT + "\\" + fname)
    flocation = settings.MEDIA_ROOT + "/registration_form/" + fname
    doc = SimpleDocTemplate(
        flocation, rightMargin=15, leftMargin=15, topMargin=0, bottomMargin=0
    )
    styles = getSampleStyleSheet()

    Story = [Spacer(1, 0.5)]
    Story.append(Spacer(1, 0.4 * inch))
    style = styles["Normal"]

    style = getSampleStyleSheet()
    normal = style["Normal"]
    normal.alignment = TA_CENTER
    normal.fontName = "Helvetica"
    normal.fontSize = 12
    normal.leading = 18
    title = "<b>EZOD UNIVERSITY OF TECHNOLOGY, ADAMA</b>"  # TODO: Make this dynamic
    title = Paragraph(title.upper(), normal)
    Story.append(title)
    style = getSampleStyleSheet()

    school = style["Normal"]
    school.alignment = TA_CENTER
    school.fontName = "Helvetica"
    school.fontSize = 10
    school.leading = 18
    school_title = (
        "<b>SCHOOL OF ELECTRICAL ENGINEERING & COMPUTING</b>"  # TODO: Make this dynamic
    )
    school_title = Paragraph(school_title.upper(), school)
    Story.append(school_title)

    style = getSampleStyleSheet()
    Story.append(Spacer(1, 0.1 * inch))
    department = style["Normal"]
    department.alignment = TA_CENTER
    department.fontName = "Helvetica"
    department.fontSize = 9
    department.leading = 18
    department_title = (
        "<b>DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING</b>"  # TODO: Make this dynamic
    )
    department_title = Paragraph(department_title, department)
    Story.append(department_title)
    Story.append(Spacer(1, 0.3 * inch))

    title = "<b><u>STUDENT COURSE REGISTRATION FORM</u></b>"
    title = Paragraph(title.upper(), normal)
    Story.append(title)
    student = Student.objects.get(student__pk=request.user.id)

    style_right = ParagraphStyle(name="right", parent=styles["Normal"])
    tbl_data = [
        [
            Paragraph(
                "<b>Registration Number : " + request.user.username.upper() + "</b>",
                styles["Normal"],
            )
        ],
        [
            Paragraph(
                "<b>Name : " + request.user.get_full_name.upper() + "</b>",
                styles["Normal"],
            )
        ],
        [
            Paragraph(
                "<b>Session : " + current_session.session.upper() + "</b>",
                styles["Normal"],
            ),
            Paragraph("<b>Level: " + student.level + "</b>", styles["Normal"]),
        ],
    ]
    tbl = Table(tbl_data)
    Story.append(tbl)
    Story.append(Spacer(1, 0.6 * inch))

    style = getSampleStyleSheet()
    semester = style["Normal"]
    semester.alignment = TA_LEFT
    semester.fontName = "Helvetica"
    semester.fontSize = 9
    semester.leading = 18
    semester_title = "<b>FIRST SEMESTER</b>"
    semester_title = Paragraph(semester_title, semester)
    Story.append(semester_title)

    elements = []

    # FIRST SEMESTER
    count = 0
    header = [
        (
            "S/No",
            "Course Code",
            "Course Title",
            "Unit",
            Paragraph("Name, Siganture of course lecturer & Date", style["Normal"]),
        )
    ]
    table_header = Table(header, 1 * [1.4 * inch], 1 * [0.5 * inch])
    table_header.setStyle(
        TableStyle(
            [
                ("ALIGN", (-2, -2), (-2, -2), "CENTER"),
                ("VALIGN", (-2, -2), (-2, -2), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
                ("ALIGN", (-4, 0), (-4, 0), "LEFT"),
                ("VALIGN", (-4, 0), (-4, 0), "MIDDLE"),
                ("ALIGN", (-3, 0), (-3, 0), "LEFT"),
                ("VALIGN", (-3, 0), (-3, 0), "MIDDLE"),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    Story.append(table_header)

    first_semester_unit = 0
    for course in courses:
        if course.course.semester == FIRST:
            first_semester_unit += int(course.course.credit)
            data = [
                (
                    count + 1,
                    course.course.code.upper(),
                    Paragraph(course.course.title, style["Normal"]),
                    course.course.credit,
                    "",
                )
            ]
            color = colors.black
            count += 1
            table_body = Table(data, 1 * [1.4 * inch], 1 * [0.3 * inch])
            table_body.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (-2, -2), (-2, -2), "CENTER"),
                        ("ALIGN", (1, 0), (1, 0), "CENTER"),
                        ("ALIGN", (0, 0), (0, 0), "CENTER"),
                        ("ALIGN", (-4, 0), (-4, 0), "LEFT"),
                        ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
                        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                        ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                    ]
                )
            )
            Story.append(table_body)

    style = getSampleStyleSheet()
    semester = style["Normal"]
    semester.alignment = TA_LEFT
    semester.fontName = "Helvetica"
    semester.fontSize = 8
    semester.leading = 18
    semester_title = (
        "<b>Total Second First Credit : " + str(first_semester_unit) + "</b>"
    )
    semester_title = Paragraph(semester_title, semester)
    Story.append(semester_title)

    # FIRST SEMESTER ENDS HERE
    Story.append(Spacer(1, 0.6 * inch))

    style = getSampleStyleSheet()
    semester = style["Normal"]
    semester.alignment = TA_LEFT
    semester.fontName = "Helvetica"
    semester.fontSize = 9
    semester.leading = 18
    semester_title = "<b>SECOND SEMESTER</b>"
    semester_title = Paragraph(semester_title, semester)
    Story.append(semester_title)
    # SECOND SEMESTER
    count = 0
    header = [
        (
            "S/No",
            "Course Code",
            "Course Title",
            "Unit",
            Paragraph(
                "<b>Name, Signature of course lecturer & Date</b>", style["Normal"]
            ),
        )
    ]
    table_header = Table(header, 1 * [1.4 * inch], 1 * [0.5 * inch])
    table_header.setStyle(
        TableStyle(
            [
                ("ALIGN", (-2, -2), (-2, -2), "CENTER"),
                ("VALIGN", (-2, -2), (-2, -2), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
                ("ALIGN", (-4, 0), (-4, 0), "LEFT"),
                ("VALIGN", (-4, 0), (-4, 0), "MIDDLE"),
                ("ALIGN", (-3, 0), (-3, 0), "LEFT"),
                ("VALIGN", (-3, 0), (-3, 0), "MIDDLE"),
                ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    Story.append(table_header)

    second_semester_unit = 0
    for course in courses:
        if course.course.semester == SECOND:
            second_semester_unit += int(course.course.credit)
            data = [
                (
                    count + 1,
                    course.course.code.upper(),
                    Paragraph(course.course.title, style["Normal"]),
                    course.course.credit,
                    "",
                )
            ]
            color = colors.black
            count += 1
            table_body = Table(data, 1 * [1.4 * inch], 1 * [0.3 * inch])
            table_body.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (-2, -2), (-2, -2), "CENTER"),
                        ("ALIGN", (1, 0), (1, 0), "CENTER"),
                        ("ALIGN", (0, 0), (0, 0), "CENTER"),
                        ("ALIGN", (-4, 0), (-4, 0), "LEFT"),
                        ("TEXTCOLOR", (0, -1), (-1, -1), colors.black),
                        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                        ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                    ]
                )
            )
            Story.append(table_body)

    style = getSampleStyleSheet()
    semester = style["Normal"]
    semester.alignment = TA_LEFT
    semester.fontName = "Helvetica"
    semester.fontSize = 8
    semester.leading = 18
    semester_title = (
        "<b>Total Second Semester Credit : " + str(second_semester_unit) + "</b>"
    )
    semester_title = Paragraph(semester_title, semester)
    Story.append(semester_title)

    Story.append(Spacer(1, 2))
    style = getSampleStyleSheet()
    certification = style["Normal"]
    certification.alignment = TA_JUSTIFY
    certification.fontName = "Helvetica"
    certification.fontSize = 8
    certification.leading = 18
    student = Student.objects.get(student__pk=request.user.id)
    certification_text = (
        "CERTIFICATION OF REGISTRATION: I certify that <b>"
        + str(request.user.get_full_name.upper())
        + "</b>\
    has been duly registered for the <b>"
        + student.level
        + " level </b> of study in the department\
    of COMPUTER SICENCE & ENGINEERING and that the courses and credits \
    registered are as approved by the senate of the University"
    )
    certification_text = Paragraph(certification_text, certification)
    Story.append(certification_text)

    # FIRST SEMESTER ENDS HERE

    logo = settings.STATICFILES_DIRS[0] + "/img/dj-lms.png"
    im_logo = Image(logo, 1 * inch, 1 * inch)
    im_logo.__setattr__("_offs_x", -218)
    im_logo.__setattr__("_offs_y", 480)
    Story.append(im_logo)

    picture = settings.BASE_DIR + request.user.get_picture()
    im = Image(picture, 1.0 * inch, 1.0 * inch)
    im.__setattr__("_offs_x", 218)
    im.__setattr__("_offs_y", 550)
    Story.append(im)

    doc.build(Story)
    fs = FileSystemStorage(settings.MEDIA_ROOT + "/registration_form")
    with fs.open(fname) as pdf:
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = "inline; filename=" + fname + ""
        return response
    return response
