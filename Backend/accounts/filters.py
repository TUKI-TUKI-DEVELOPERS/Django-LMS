from django.db.models import Q
import django_filters
from .models import User, Student, GENDERS, LEVEL


class LecturerFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_expr="icontains", label="Usuario")
    name = django_filters.CharFilter(method="filter_by_name", label="Nombre")
    email = django_filters.CharFilter(lookup_expr="icontains", label="Correo")
    phone = django_filters.CharFilter(lookup_expr="icontains", label="Teléfono")
    address = django_filters.CharFilter(lookup_expr="icontains", label="Dirección")
    gender = django_filters.ChoiceFilter(choices=GENDERS, label="Género")
    is_active = django_filters.BooleanFilter(label="Activo")
    date_joined = django_filters.DateFromToRangeFilter(label="Fecha de Registro")

    class Meta:
        model = User
        fields = ["username", "email", "phone", "address", "gender", "is_active", "date_joined"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Change html classes and placeholders
        self.filters["username"].field.widget.attrs.update(
            {"class": "form-control", "placeholder": "Buscar por usuario"}
        )
        self.filters["name"].field.widget.attrs.update(
            {"class": "form-control", "placeholder": "Buscar por nombre"}
        )
        self.filters["email"].field.widget.attrs.update(
            {"class": "form-control", "placeholder": "Buscar por correo"}
        )
        self.filters["phone"].field.widget.attrs.update(
            {"class": "form-control", "placeholder": "Buscar por teléfono"}
        )
        self.filters["address"].field.widget.attrs.update(
            {"class": "form-control", "placeholder": "Buscar por dirección"}
        )
        self.filters["gender"].field.widget.attrs.update(
            {"class": "form-select"}
        )
        self.filters["is_active"].field.widget.attrs.update(
            {"class": "form-check-input"}
        )
        self.filters["date_joined"].field.widget.attrs.update(
            {"class": "form-control"}
        )

    def filter_by_name(self, queryset, name, value):
        return queryset.filter(
            Q(first_name__icontains=value) | Q(last_name__icontains=value)
        )


class StudentFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(
        field_name="student__username", lookup_expr="icontains", label="Usuario"
    )
    name = django_filters.CharFilter(
        field_name="student__name", method="filter_by_name", label="Nombre"
    )
    email = django_filters.CharFilter(
        field_name="student__email", lookup_expr="icontains", label="Correo"
    )
    phone = django_filters.CharFilter(
        field_name="student__phone", lookup_expr="icontains", label="Teléfono"
    )
    address = django_filters.CharFilter(
        field_name="student__address", lookup_expr="icontains", label="Dirección"
    )
    program = django_filters.CharFilter(
        field_name="program__title", lookup_expr="icontains", label="Programa"
    )
    level = django_filters.ChoiceFilter(choices=LEVEL, label="Nivel")
    gender = django_filters.ChoiceFilter(
        field_name="student__gender", choices=GENDERS, label="Género"
    )
    is_active = django_filters.BooleanFilter(
        field_name="student__is_active", label="Activo"
    )
    date_joined = django_filters.DateFromToRangeFilter(
        field_name="student__date_joined", label="Fecha de Registro"
    )

    class Meta:
        model = Student
        fields = [
            "username",
            "name",
            "email",
            "phone",
            "address",
            "program",
            "level",
            "gender",
            "is_active",
            "date_joined",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Change html classes and placeholders
        self.filters["username"].field.widget.attrs.update(
            {"class": "form-control", "placeholder": "Buscar por usuario"}
        )
        self.filters["name"].field.widget.attrs.update(
            {"class": "form-control", "placeholder": "Buscar por nombre"}
        )
        self.filters["email"].field.widget.attrs.update(
            {"class": "form-control", "placeholder": "Buscar por correo"}
        )
        self.filters["phone"].field.widget.attrs.update(
            {"class": "form-control", "placeholder": "Buscar por teléfono"}
        )
        self.filters["address"].field.widget.attrs.update(
            {"class": "form-control", "placeholder": "Buscar por dirección"}
        )
        self.filters["program"].field.widget.attrs.update(
            {"class": "form-control", "placeholder": "Buscar por programa"}
        )
        self.filters["level"].field.widget.attrs.update(
            {"class": "form-select"}
        )
        self.filters["gender"].field.widget.attrs.update(
            {"class": "form-select"}
        )
        self.filters["is_active"].field.widget.attrs.update(
            {"class": "form-check-input"}
        )
        self.filters["date_joined"].field.widget.attrs.update(
            {"class": "form-control"}
        )

    def filter_by_name(self, queryset, name, value):
        return queryset.filter(
            Q(student__first_name__icontains=value)
            | Q(student__last_name__icontains=value)
        )
