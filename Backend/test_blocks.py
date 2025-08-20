#!/usr/bin/env python3
"""
Script de prueba para verificar la creación de bloques de lecciones
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from course.models import Course, Module, Lesson, LessonBlock
from course.forms import LessonBlockForm

def test_block_creation():
    """Prueba la creación de un bloque de lección"""
    print("=== PRUEBA DE CREACIÓN DE BLOQUES ===")
    
    try:
        # Obtener la primera lección disponible
        lesson = Lesson.objects.filter(is_active=True).first()
        if not lesson:
            print("❌ No se encontraron lecciones activas")
            return
        
        print(f"✅ Lección encontrada: {lesson.title}")
        print(f"   Módulo: {lesson.module.title}")
        print(f"   Curso: {lesson.module.course.title}")
        
        # Verificar bloques existentes
        existing_blocks = lesson.blocks.filter(is_active=True).order_by('order')
        print(f"   Bloques existentes: {existing_blocks.count()}")
        for block in existing_blocks:
            print(f"     - {block.block_type} (orden: {block.order})")
        
        # Crear un bloque de prueba
        print("\n--- Creando bloque de prueba ---")
        block_data = {
            'block_type': 'text',
            'title': 'Bloque de Prueba',
            'order': 1,
            'text_content': 'Este es un bloque de prueba para verificar la funcionalidad.',
            'width': '100%',
            'is_active': True
        }
        
        form = LessonBlockForm(block_data)
        if form.is_valid():
            print("✅ Formulario válido")
            
            # Asignar orden
            if not block_data.get('order'):
                last_block = LessonBlock.objects.filter(lesson=lesson, is_active=True).order_by('-order').first()
                order = (last_block.order + 1) if last_block and last_block.order > 0 else 1
                block_data['order'] = order
                print(f"   Orden asignado: {order}")
            
            # Crear y guardar el bloque
            block = form.save(commit=False)
            block.lesson = lesson
            block.order = block_data['order']
            
            print(f"   Guardando bloque: {block.block_type}, orden: {block.order}")
            block.save()
            
            print(f"✅ Bloque creado con ID: {block.id}")
            
            # Verificar que se guardó correctamente
            saved_block = LessonBlock.objects.filter(id=block.id, lesson=lesson, is_active=True).first()
            if saved_block:
                print(f"✅ Bloque recuperado de la BD: {saved_block}")
                print(f"   Orden: {saved_block.order}")
                print(f"   Tipo: {saved_block.block_type}")
                print(f"   Título: {saved_block.title}")
            else:
                print("❌ No se pudo recuperar el bloque de la BD")
            
            # Verificar bloques después de la creación
            blocks_after = lesson.blocks.filter(is_active=True).order_by('order')
            print(f"\n   Bloques después de crear: {blocks_after.count()}")
            for block in blocks_after:
                print(f"     - {block.block_type} (orden: {block.order})")
            
        else:
            print("❌ Formulario inválido")
            print(f"   Errores: {form.errors}")
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_block_creation()
