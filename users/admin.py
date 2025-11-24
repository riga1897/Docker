from django.contrib import admin

from users.models import Payment, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Админ-панель для модели User."""

    list_display = ("email", "first_name", "last_name", "phone", "city", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "city")
    search_fields = ("email", "first_name", "last_name", "phone")
    ordering = ("-date_joined",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Админ-панель для модели Payment."""

    list_display = ("owner", "payment_date", "course", "lesson", "amount", "payment_method")
    list_filter = ("payment_method", "payment_date", "course", "lesson")
    search_fields = ("owner__email", "course__title", "lesson__title")
    ordering = ("-payment_date",)
    date_hierarchy = "payment_date"
