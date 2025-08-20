from django.urls import path
from . import views

app_name = "course"

urlpatterns = [
    path("", views.CourseFilterView.as_view(), name="course_list"),
    path("programs/", views.ProgramFilterView.as_view(), name="programs"),
    path("program/add/", views.program_add, name="add_program"),
    path("program/<int:pk>/", views.program_detail, name="program_detail"),
    path("program/<int:pk>/edit/", views.program_edit, name="program_edit"),
    path("program/<int:pk>/delete/", views.program_delete, name="program_delete"),
    path("course/add/<int:pk>/", views.course_add, name="course_add"),
    path("course/<slug>/edit/", views.course_edit, name="course_edit"),
    path("course/<slug>/delete/", views.course_delete, name="course_delete"),
    path("my_courses/", views.user_course_list, name="user_course_list"),
    path("course/registration/", views.course_registration, name="course_registration"),
    path("course/drop/", views.course_drop, name="course_drop"),
    # Mantener las rutas específicas antes de la genérica `course/<slug>/`
    path("course/<slug>/modules/", views.course_modules, name="course_modules"),
    path("course/<slug>/module/<int:module_id>/", views.module_detail, name="module_detail"),
    path("course/<slug>/module/<int:module_id>/lesson/<int:lesson_id>/", views.lesson_detail, name="lesson_detail"),
    path("course/<slug>/module/<int:module_id>/lesson/<int:lesson_id>/complete/", views.mark_lesson_complete, name="mark_lesson_complete"),
    path("course/<slug>/module/<int:module_id>/lesson/<int:lesson_id>/submit-activity/", views.submit_activity, name="submit_activity"),
    path("course/<slug>/module/<int:module_id>/lesson/<int:lesson_id>/quiz/", views.take_quiz, name="take_quiz"),
    # URLs para profesores y administradores
    path("course/<slug>/modules/create/", views.module_create, name="module_create"),
    path("course/<slug>/module/<int:module_id>/edit/", views.module_edit, name="module_edit"),
    path("course/<slug>/module/<int:module_id>/delete/", views.module_delete, name="module_delete"),
    path("course/<slug>/module/<int:module_id>/lessons/create/", views.lesson_create, name="lesson_create"),
    path("course/<slug>/module/<int:module_id>/lesson/<int:lesson_id>/edit/", views.lesson_edit, name="lesson_edit"),
    path("course/<slug>/module/<int:module_id>/lesson/<int:lesson_id>/delete/", views.lesson_delete, name="lesson_delete"),
    path("course/<slug>/module/<int:module_id>/lesson/<int:lesson_id>/reactivate/", views.lesson_reactivate, name="lesson_reactivate"),
    path("course/<slug>/module/<int:module_id>/lesson/<int:lesson_id>/deactivate/", views.lesson_deactivate, name="lesson_deactivate"),
    # URLs para el canvas y bloques de contenido
    path("course/<slug>/module/<int:module_id>/lesson/<int:lesson_id>/canvas/", views.lesson_canvas, name="lesson_canvas"),
    path("course/<slug>/module/<int:module_id>/lesson/<int:lesson_id>/block/create/", views.block_create, name="block_create"),
    path("course/<slug>/module/<int:module_id>/lesson/<int:lesson_id>/block/<int:block_id>/edit/", views.block_edit, name="block_edit"),
    path("course/<slug>/module/<int:module_id>/lesson/<int:lesson_id>/block/<int:block_id>/delete/", views.block_delete, name="block_delete"),
    path("course/<slug>/module/<int:module_id>/lesson/<int:lesson_id>/blocks/reorder/", views.block_reorder, name="block_reorder"),
    # URLs para subida de archivos y videos
    path("course/<slug>/upload/", views.handle_file_upload, name="upload_file_view"),
    path("course/<slug>/upload/video/", views.handle_video_upload, name="upload_video_view"),
    path("course/<slug>/upload/<int:file_id>/edit/", views.handle_file_edit, name="edit_file_view"),
    path("course/<slug>/upload/<int:file_id>/delete/", views.handle_file_delete, name="delete_file_view"),
    path("course/<slug>/video/<slug:video_slug>/", views.handle_video_single, name="video_single_view"),
    path("course/<slug>/video/<slug:video_slug>/edit/", views.handle_video_edit, name="edit_video_view"),
    path("course/<slug>/video/<slug:video_slug>/delete/", views.handle_video_delete, name="delete_video_view"),
    # URLs para asignación de cursos (deben ir antes de la ruta genérica <slug>)
    path("course/allocation/", views.CourseAllocationFormView.as_view(), name="course_allocation"),
    path("course/allocated/", views.CourseAllocationFilterView.as_view(), name="course_allocation_view"),
    path("allocated_course/<int:pk>/edit/", views.edit_allocated_course, name="edit_allocated_course"),
    path("course/<int:pk>/deallocate/", views.deallocate_course, name="course_deallocate"),
    # Ruta genérica al final para evitar capturar otras rutas como 'allocated'
    path("course/<slug>/", views.course_single, name="course_single"),
]
