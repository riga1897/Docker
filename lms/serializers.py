"""Сериализаторы для LMS API."""

from rest_framework import serializers

from lms.models import Course, Lesson
from lms.services import calculate_lessons_count, check_user_subscription
from lms.validators import validate_youtube_url


class LessonSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Lesson.

    Включает все поля модели включая ForeignKey на Course.
    Валидирует video_url - разрешены только ссылки на YouTube.
    """

    video_url = serializers.URLField(max_length=500, validators=[validate_youtube_url])

    class Meta:  # type: ignore[misc]
        model = Lesson
        fields = ["id", "course", "title", "description", "preview", "video_url", "owner", "created_at", "updated_at"]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class CourseSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Course.

    Включает все поля модели для CRUD операций.
    Добавлены:
    - lessons_count: количество уроков в курсе
    - lessons: полная информация по всем урокам курса
    - is_subscribed: подписан ли текущий пользователь на курс
    """

    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:  # type: ignore[misc]
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "preview",
            "owner",
            "created_at",
            "updated_at",
            "lessons_count",
            "lessons",
            "is_subscribed",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    @staticmethod
    def get_lessons_count(obj: Course) -> int:
        """
        Возвращает количество уроков в курсе.

        Делегирует вычисление в Service Layer.
        """
        return calculate_lessons_count(obj)

    def get_is_subscribed(self, obj: Course) -> bool:
        """
        Проверяет, подписан ли текущий пользователь на курс.

        Делегирует проверку в Service Layer.
        Безопасно работает даже без request context (например, в admin или CLI).

        Returns:
            True если пользователь аутентифицирован и подписан на курс,
            False в противном случае.
        """
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            return False

        user = request.user if request.user.is_authenticated else None
        return check_user_subscription(obj, user)
