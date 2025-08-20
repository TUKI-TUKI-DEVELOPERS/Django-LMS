from django.urls import path
from .views import (
    add_score,
    add_score_for,
    grade_result,
    assessment_result,
    course_registration_form,
    result_sheet_pdf_view,
    certificate_list,
    certificate_pdf_view,
    certificate_admin_list,
    certificate_admin_detail,
    certificate_manage,
    certificate_generate,
    certificate_bulk_generate,
    certificate_toggle_status,
    program_course_grades,
)


urlpatterns = [
    path("manage-score/", add_score, name="add_score"),
    path("manage-score/<int:id>/", add_score_for, name="add_score_for"),
    path("grade/", grade_result, name="grade_results"),
    path("assessment/", assessment_result, name="ass_results"),
    path("result/print/<int:id>/", result_sheet_pdf_view, name="result_sheet_pdf_view"),
    path("certificates/", certificate_list, name="certificate_list"),
    path("certificates/print/<int:id>/", certificate_pdf_view, name="certificate_pdf_view"),
    path("certificates/admin/", certificate_admin_list, name="certificate_admin_list"),
    path("certificates/admin/<int:id>/", certificate_admin_detail, name="certificate_admin_detail"),
    path("certificates/manage/", certificate_manage, name="certificate_manage"),
    path("certificates/generate/<int:id>/", certificate_generate, name="certificate_generate"),
    path("certificates/bulk_generate/", certificate_bulk_generate, name="certificate_bulk_generate"),
    path("certificates/toggle/<int:id>/", certificate_toggle_status, name="certificate_toggle_status"),
    path("program/grades/", program_course_grades, name="program_course_grades"),
    path(
        "registration/form/", course_registration_form, name="course_registration_form"
    ),
]
