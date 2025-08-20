#!/usr/bin/env python3
"""
Script para crear datos de prueba básicos para el sistema de calificaciones
"""
import os
import django
from django.contrib.auth import get_user_model
from django.utils import timezone

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Session, Semester
from course.models import Program, Course, CourseAllocation
from accounts.models import Student, User
from result.models import TakenCourse

def create_test_data():
    """Crear datos de prueba básicos"""
    print("Creando datos de prueba...")
    
    # Crear sesión actual
    session, created = Session.objects.get_or_create(
        session="2024/2025",
        defaults={
            'is_current_session': True,
            'next_session_begins': timezone.now().date()
        }
    )
    if created:
        print(f"Sesión creada: {session.session}")
    else:
        print(f"Sesión existente: {session.session}")
    
    # Crear semestre actual
    semester, created = Semester.objects.get_or_create(
        semester="First",
        defaults={
            'is_current_semester': True,
            'session': session,
            'next_semester_begins': timezone.now().date()
        }
    )
    if created:
        print(f"Semestre creado: {semester.semester}")
    else:
        print(f"Semestre existente: {semester.semester}")
    
    # Crear programa
    program, created = Program.objects.get_or_create(
        title="Computer Science",
        defaults={
            'summary': "Programa de Ciencias de la Computación"
        }
    )
    if created:
        print(f"Programa creado: {program.title}")
    else:
        print(f"Programa existente: {program.title}")
    
    # Crear curso
    course, created = Course.objects.get_or_create(
        code="CS101",
        defaults={
            'title': "Introduction to Programming",
            'slug': 'introduction-to-programming',
            'credit': 3,
            'summary': "Curso introductorio a la programación",
            'program': program,
            'level': "Beginner",
            'year': 1,
            'semester': "First",
            'is_elective': False
        }
    )
    if created:
        print(f"Curso creado: {course.title}")
    else:
        print(f"Curso existente: {course.title}")
    
    # Crear usuario profesor
    User = get_user_model()
    lecturer_user, created = User.objects.get_or_create(
        username='profesor1',
        defaults={
            'email': 'profesor1@test.com',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'is_lecturer': True,
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        lecturer_user.set_password('testpass123')
        lecturer_user.save()
        print(f"Usuario profesor creado: {lecturer_user.username}")
    else:
        print(f"Usuario profesor existente: {lecturer_user.username}")
    
    # Crear profesor (usar directamente el usuario)
    lecturer = lecturer_user
    
    # Crear asignación de curso
    allocation, created = CourseAllocation.objects.get_or_create(
        lecturer=lecturer,
        session=session
    )
    if created:
        print(f"Asignación de curso creada")
    else:
        print(f"Asignación de curso existente")
    
    # Agregar el curso a la asignación
    allocation.courses.add(course)
    print(f"Curso {course.title} agregado a la asignación")
    
    # Crear usuario estudiante
    student_user, created = User.objects.get_or_create(
        username='estudiante1',
        defaults={
            'email': 'estudiante1@test.com',
            'first_name': 'María',
            'last_name': 'García',
            'is_student': True
        }
    )
    if created:
        student_user.set_password('testpass123')
        student_user.save()
        print(f"Usuario estudiante creado: {student_user.username}")
    else:
        print(f"Usuario estudiante existente: {student_user.username}")
    
    # Crear estudiante
    student, created = Student.objects.get_or_create(
        user=student_user,
        defaults={
            'level': "Beginner",
            'program': program
        }
    )
    if created:
        print(f"Estudiante creado: {student.user.get_full_name()}")
    else:
        print(f"Estudiante existente: {student.user.get_full_name()}")
    
    # Crear curso tomado
    taken_course, created = TakenCourse.objects.get_or_create(
        student=student,
        course=course,
        defaults={
            'assignment': 0.0,
            'mid_exam': 0.0,
            'quiz': 0.0,
            'attendance': 0.0,
            'final_exam': 0.0,
            'total': 0.0
        }
    )
    if created:
        print(f"Curso tomado creado: {student.user.get_full_name()} - {course.title}")
    else:
        print(f"Curso tomado existente: {student.user.get_full_name()} - {course.title}")
    
    print("\nDatos de prueba creados exitosamente!")
    print(f"Puedes acceder con:")
    print(f"Profesor: usuario=profesor1, contraseña=testpass123")
    print(f"Estudiante: usuario=estudiante1, contraseña=testpass123")
    print(f"URL del curso: http://localhost:8000/es/result/manage-score/1/")

if __name__ == '__main__':
    create_test_data()
