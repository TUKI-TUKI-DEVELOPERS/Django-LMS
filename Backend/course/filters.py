from django.db.models import Q
import django_filters
from .models import Program, CourseAllocation, Course


class ProgramFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains", label="")

    class Meta:
        model = Program
        fields = ["title"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Change html classes and placeholders
        self.filters["title"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "Nombre del programa"}
        )


class CourseFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains", label="")
    code = django_filters.CharFilter(lookup_expr="icontains", label="")
    program = django_filters.ModelChoiceFilter(queryset=Program.objects.all(), label="")
    semester = django_filters.CharFilter(lookup_expr="icontains", label="")
    is_active = django_filters.BooleanFilter(label="")

    class Meta:
        model = Course
        fields = ["title", "code", "program", "semester", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Change html classes and placeholders
        self.filters["title"].field.widget.attrs.update(
            {"class": "form-control", "placeholder": "Título del curso"}
        )
        self.filters["code"].field.widget.attrs.update(
            {"class": "form-control", "placeholder": "Código del curso"}
        )
        self.filters["program"].field.widget.attrs.update(
            {"class": "form-control"}
        )
        self.filters["semester"].field.widget.attrs.update(
            {"class": "form-control", "placeholder": "Semestre"}
        )
        self.filters["is_active"].field.widget.attrs.update(
            {"class": "form-check-input"}
        )


class CourseAllocationFilter(django_filters.FilterSet):
    lecturer = django_filters.CharFilter(method="filter_by_lecturer", label="")
    course = django_filters.filters.CharFilter(method="filter_by_course", label="")

    class Meta:
        model = CourseAllocation
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Change html classes and placeholders
        self.filters["lecturer"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "Profesor"}
        )
        self.filters["course"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "Curso"}
        )

    def filter_by_lecturer(self, queryset, name, value):
        return queryset.filter(
            Q(lecturer__first_name__icontains=value)
            | Q(lecturer__last_name__icontains=value)
        )

    def filter_by_course(self, queryset, name, value):
        return queryset.filter(courses__title__icontains=value)
