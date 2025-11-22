"""Тесты для обновлённого CourseSerializer с lessons_count и вложенными lessons."""

import pytest
from rest_framework.test import APIClient, APIRequestFactory

from lms.models import Course, Lesson
from lms.serializers import CourseSerializer
from users.models import User


@pytest.fixture
def test_user() -> User:
    """Создать тестового пользователя."""
    return User.objects.create_user(email="test@example.com", password="testpass123")


@pytest.fixture
def api_request_factory() -> APIRequestFactory:
    """API request factory для тестов сериализаторов."""
    return APIRequestFactory()


@pytest.fixture
def api_client() -> APIClient:
    """API клиент для интеграционных тестов."""
    return APIClient()


@pytest.mark.django_db
class TestCourseSerializerWithLessons:
    """Тесты для CourseSerializer с подсчётом и вложением уроков."""

    def test_course_serializer_lessons_count_zero(
        self, api_request_factory: APIRequestFactory, test_user: User
    ) -> None:
        """Тест: lessons_count = 0 для курса без уроков."""
        course = Course.objects.create(title="Empty Course", description="No lessons yet", owner=test_user)

        request = api_request_factory.get("/")
        request.user = test_user
        serializer = CourseSerializer(course, context={"request": request})

        assert "lessons_count" in serializer.data
        assert serializer.data["lessons_count"] == 0

    def test_course_serializer_lessons_count_multiple(
        self, api_request_factory: APIRequestFactory, test_user: User
    ) -> None:
        """Тест: lessons_count корректно подсчитывает уроки."""
        course = Course.objects.create(title="Python Course", description="Learn Python", owner=test_user)

        Lesson.objects.create(
            course=course, title="Lesson 1", description="Intro", video_url="https://youtube.com/1", owner=test_user
        )
        Lesson.objects.create(
            course=course, title="Lesson 2", description="Basics", video_url="https://youtube.com/2", owner=test_user
        )
        Lesson.objects.create(
            course=course, title="Lesson 3", description="Advanced", video_url="https://youtube.com/3", owner=test_user
        )

        request = api_request_factory.get("/")
        request.user = test_user
        serializer = CourseSerializer(course, context={"request": request})

        assert serializer.data["lessons_count"] == 3

    def test_course_serializer_has_nested_lessons(
        self, api_request_factory: APIRequestFactory, test_user: User
    ) -> None:
        """Тест: вложенное поле lessons содержит полную информацию об уроках."""
        course = Course.objects.create(title="Django Course", description="Learn Django", owner=test_user)

        Lesson.objects.create(
            course=course,
            title="Django Models",
            description="Learn about models",
            video_url="https://youtube.com/django-models",
            owner=test_user,
        )
        Lesson.objects.create(
            course=course,
            title="Django Views",
            description="Learn about views",
            video_url="https://youtube.com/django-views",
            owner=test_user,
        )

        request = api_request_factory.get("/")
        request.user = test_user
        serializer = CourseSerializer(course, context={"request": request})

        assert "lessons" in serializer.data
        assert len(serializer.data["lessons"]) == 2

        lessons_data = serializer.data["lessons"]
        assert lessons_data[0]["title"] == "Django Models"
        assert lessons_data[0]["description"] == "Learn about models"
        assert lessons_data[0]["video_url"] == "https://youtube.com/django-models"

        assert lessons_data[1]["title"] == "Django Views"

    def test_course_serializer_lessons_empty_list(
        self, api_request_factory: APIRequestFactory, test_user: User
    ) -> None:
        """Тест: lessons - пустой список для курса без уроков."""
        course = Course.objects.create(title="Empty Course", description="No lessons", owner=test_user)

        request = api_request_factory.get("/")
        request.user = test_user
        serializer = CourseSerializer(course, context={"request": request})

        assert "lessons" in serializer.data
        assert serializer.data["lessons"] == []

    def test_course_serializer_all_fields_present(
        self, api_request_factory: APIRequestFactory, test_user: User
    ) -> None:
        """Тест: все поля присутствуют в сериализованных данных."""
        course = Course.objects.create(
            title="Complete Course", description="Full course with lessons", owner=test_user
        )

        Lesson.objects.create(
            course=course, title="Lesson 1", description="First", video_url="https://youtube.com/1", owner=test_user
        )

        request = api_request_factory.get("/")
        request.user = test_user
        serializer = CourseSerializer(course, context={"request": request})

        expected_fields = {
            "id",
            "title",
            "description",
            "preview",
            "created_at",
            "updated_at",
            "lessons_count",
            "lessons",
            "is_subscribed",
            "owner",
        }
        assert set(serializer.data.keys()) == expected_fields

    def test_course_api_endpoint_returns_lessons_data(self, test_user: User) -> None:
        """Интеграционный тест: API эндпоинт возвращает lessons_count и lessons."""
        from django.urls import reverse
        from rest_framework.test import APIClient

        authenticated_client = APIClient()
        authenticated_client.force_authenticate(user=test_user)

        course = Course.objects.create(title="API Test Course", description="Testing API", owner=test_user)

        Lesson.objects.create(
            course=course, title="Lesson 1", description="First", video_url="https://youtube.com/1", owner=test_user
        )
        Lesson.objects.create(
            course=course, title="Lesson 2", description="Second", video_url="https://youtube.com/2", owner=test_user
        )

        url = reverse("lms:course-detail", kwargs={"pk": course.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.data["lessons_count"] == 2
        assert len(response.data["lessons"]) == 2
        assert response.data["lessons"][0]["title"] == "Lesson 1"
        assert response.data["lessons"][1]["title"] == "Lesson 2"

    def test_course_list_includes_lessons_count(self, test_user: User) -> None:
        """Интеграционный тест: список курсов включает lessons_count."""
        from django.urls import reverse
        from rest_framework.test import APIClient

        authenticated_client = APIClient()
        authenticated_client.force_authenticate(user=test_user)

        course1 = Course.objects.create(title="Course 1", description="First course", owner=test_user)
        course2 = Course.objects.create(title="Course 2", description="Second course", owner=test_user)

        Lesson.objects.create(
            course=course1, title="Lesson 1", description="Test", video_url="https://youtube.com/1", owner=test_user
        )
        Lesson.objects.create(
            course=course2, title="Lesson 2", description="Test", video_url="https://youtube.com/2", owner=test_user
        )
        Lesson.objects.create(
            course=course2, title="Lesson 3", description="Test", video_url="https://youtube.com/3", owner=test_user
        )

        url = reverse("lms:course-list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2

        for course_data in response.data["results"]:
            assert "lessons_count" in course_data
            assert "lessons" in course_data


@pytest.mark.django_db
class TestCourseSerializerWithoutRequestContext:
    """Regression тесты для CourseSerializer без request context."""

    def test_course_serializer_without_request_context(self, test_user: User) -> None:
        """Тест: сериализатор работает без request context (например, в admin или CLI)."""
        course = Course.objects.create(title="Test Course", description="Test", owner=test_user)

        Lesson.objects.create(
            course=course, title="Lesson 1", description="Test", video_url="https://youtube.com/1", owner=test_user
        )

        serializer = CourseSerializer(course)

        assert "lessons_count" in serializer.data
        assert serializer.data["lessons_count"] == 1
        assert "is_subscribed" in serializer.data
        assert serializer.data["is_subscribed"] is False

    def test_course_serializer_with_empty_context(self, test_user: User) -> None:
        """Тест: сериализатор работает с пустым context."""
        course = Course.objects.create(title="Test Course", description="Test", owner=test_user)

        serializer = CourseSerializer(course, context={})

        assert serializer.data["is_subscribed"] is False
        assert "lessons_count" in serializer.data
