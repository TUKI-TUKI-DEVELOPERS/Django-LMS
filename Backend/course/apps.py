from django.apps import AppConfig


class CourseConfig(AppConfig):
    name = "course"

    def ready(self):
        # Import template tags so Django registers the library
        try:
            from .templatetags import media_extras  # noqa: F401
        except Exception:
            pass
