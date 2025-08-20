from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .serializers import (
    LessonBlockSerializer,
    QuizBlockSerializer,
    QuizBlockQuestionSerializer,
    QuizBlockOptionSerializer
)
from course.models import (
    Lesson,
    LessonBlock,
    QuizBlock,
    QuizBlockQuestion,
    QuizBlockOption
)

class LessonBlockViewSet(viewsets.ModelViewSet):
    queryset = LessonBlock.objects.all()
    serializer_class = LessonBlockSerializer

    def create(self, request, *args, **kwargs):
        # Asegurar que tenemos un lesson_id
        lesson_id = request.data.get('lesson')
        if not lesson_id:
            return Response(
                {"error": "lesson_id es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener la lección o retornar 404
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Crear el serializer con los datos recibidos
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Guardar el bloque
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        block = self.get_object()
        new_order = request.data.get('order')
        
        if new_order is not None:
            # Actualizar el orden del bloque
            block.order = new_order
            block.save()
            return Response({'status': 'orden actualizado'})
        return Response(
            {'error': 'Se requiere el campo order'},
            status=status.HTTP_400_BAD_REQUEST
        )

class QuizBlockViewSet(viewsets.ModelViewSet):
    queryset = QuizBlock.objects.all()
    serializer_class = QuizBlockSerializer

class QuizBlockQuestionViewSet(viewsets.ModelViewSet):
    queryset = QuizBlockQuestion.objects.all()
    serializer_class = QuizBlockQuestionSerializer

class QuizBlockOptionViewSet(viewsets.ModelViewSet):
    queryset = QuizBlockOption.objects.all()
    serializer_class = QuizBlockOptionSerializer
