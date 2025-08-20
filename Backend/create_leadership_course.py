#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from course.models import Program, Course

def create_leadership_course():
    """Crear el curso de Liderazgo y Gestión de Equipos"""
    
    # Obtener o crear un programa para cursos profesionales
    program, created = Program.objects.get_or_create(
        title="Programa de Desarrollo Profesional",
        defaults={
            'summary': "Programa especializado en desarrollo de habilidades profesionales y liderazgo empresarial."
        }
    )
    
    if created:
        print(f"✅ Programa creado: {program.title}")
    else:
        print(f"✅ Programa encontrado: {program.title}")
    
    # Crear el curso de Liderazgo
    course_data = {
        'title': 'Liderazgo y Gestión de Equipos',
        'code': 'LGE-001',
        'summary': 'Curso especializado en desarrollar habilidades de liderazgo efectivo y gestión de equipos de trabajo.',
        'program': program,
        'level': 'Bachelor',  # Puede ser Bachelor o Master
        'year': 1,
        'semester': 'First',
        'credit': 4,
        'is_elective': False,
        
        # Información profesional
        'objectives': '''• Desarrollar habilidades de liderazgo efectivo.
• Mejorar la capacidad de motivar y dirigir equipos de trabajo.
• Fomentar la comunicación y colaboración dentro del equipo.
• Impulsar la resolución de problemas y la toma de decisiones.
• Aplicar técnicas de coaching y mentoring en el entorno laboral.
• Desarrollar estrategias para el manejo de conflictos en equipos.''',
        
        'target_audience': '''• Profesionales en posiciones de liderazgo o supervisión.
• Equipos de trabajo que buscan mejorar su rendimiento.
• Personas interesadas en desarrollar habilidades de liderazgo para avanzar en sus carreras.
• Gerentes y supervisores que necesitan fortalecer sus competencias de gestión.
• Emprendedores que requieren habilidades de liderazgo para sus proyectos.''',
        
        'duration': 40,
        'duration_unit': 'horas',
        'modality': 'e-learning',
        'category': 'desarrollo_profesional',
        
        # Información adicional
        'prerequisites': '''• Experiencia básica en gestión de equipos o supervisión de personal.
• Conocimientos fundamentales de comunicación empresarial.
• Interés en desarrollar habilidades de liderazgo.
• Disponibilidad para participar en sesiones virtuales.''',
        
        'methodology': '''• Aprendizaje basado en casos prácticos y situaciones reales.
• Sesiones interactivas con herramientas digitales.
• Ejercicios de role-playing y simulaciones.
• Análisis de casos de estudio de empresas exitosas.
• Proyectos grupales para aplicar los conocimientos.
• Evaluación continua y feedback personalizado.''',
        
        'materials_included': '''• Manual digital completo del curso.
• Videos de expertos en liderazgo.
• Plantillas y herramientas de gestión de equipos.
• Ejercicios interactivos y evaluaciones.
• Biblioteca digital con recursos adicionales.
• Certificado de finalización del curso.
• Acceso a comunidad de aprendizaje online.''',
        
        'max_students': 25,
        'certification': True,
        'is_active': True,
    }
    
    # Verificar si el curso ya existe
    existing_course = Course.objects.filter(code='LGE-001').first()
    
    if existing_course:
        print(f"⚠️  El curso ya existe: {existing_course.title}")
        # Actualizar el curso existente
        for field, value in course_data.items():
            setattr(existing_course, field, value)
        existing_course.save()
        print(f"✅ Curso actualizado: {existing_course.title}")
    else:
        # Crear el nuevo curso
        course = Course.objects.create(**course_data)
        print(f"✅ Curso creado exitosamente: {course.title}")
        print(f"   Código: {course.code}")
        print(f"   Duración: {course.full_duration}")
        print(f"   Modalidad: {course.get_modality_display()}")
        print(f"   Categoría: {course.get_category_display()}")
    
    print("\n🎯 Detalles del curso creado:")
    print("=" * 50)
    print(f"📚 Título: {course_data['title']}")
    print(f"🏷️  Código: {course_data['code']}")
    print(f"⏱️  Duración: {course_data['duration']} {course_data['duration_unit']}")
    print(f"💻 Modalidad: {course_data['modality'].title()}")
    print(f"📂 Categoría: Desarrollo Profesional y Liderazgo")
    print(f"👥 Máximo estudiantes: {course_data['max_students']}")
    print(f"🏆 Certificación: {'Sí' if course_data['certification'] else 'No'}")
    print(f"✅ Estado: {'Activo' if course_data['is_active'] else 'Inactivo'}")
    print("=" * 50)

if __name__ == '__main__':
    try:
        create_leadership_course()
        print("\n🎉 ¡Curso de Liderazgo creado exitosamente!")
        print("📍 Puedes ver el curso en: http://127.0.0.1:8000/es/programs/")
    except Exception as e:
        print(f"❌ Error al crear el curso: {e}")
        sys.exit(1)
