from django.contrib import admin

from lms.models import Course, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Админ-панель для модели Course."""

    list_display = ("title", "created_at", "updated_at")
    search_fields = ("title", "description")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Админ-панель для модели Lesson."""

    list_display = ("title", "course", "created_at", "updated_at")
    list_filter = ("course",)
    search_fields = ("title", "description", "course__title")
    ordering = ("course", "id")
