from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'blocks', views.LessonBlockViewSet)
router.register(r'quiz-blocks', views.QuizBlockViewSet)
router.register(r'quiz-questions', views.QuizBlockQuestionViewSet)
router.register(r'quiz-options', views.QuizBlockOptionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
