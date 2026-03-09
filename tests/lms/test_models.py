"""Тесты для моделей LMS."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from lms.models import Course, Lesson
from users.models import User


@pytest.fixture
def test_user() -> User:
    """Создать тестового пользователя."""
    return User.objects.create_user(email="test@example.com", password="testpass123")


@pytest.mark.django_db
class TestCourseModel:
    """Тесты для модели Course."""

    def test_course_creation_with_all_fields(self, test_user: User) -> None:
        """Тест создания курса со всеми полями."""
        preview_image = SimpleUploadedFile(name="test_preview.jpg", content=b"file_content", content_type="image/jpeg")

        course = Course.objects.create(
            owner=test_user,
            title="Python для начинающих",
            description="Полный курс по Python программированию",
            preview=preview_image,
        )

        assert course.id is not None  # type: ignore[attr-defined]
        assert course.title == "Python для начинающих"
        assert course.description == "Полный курс по Python программированию"
        assert "test_preview" in course.preview.name
        assert course.preview.name.endswith(".jpg")
        assert course.created_at is not None
        assert course.updated_at is not None

    def test_course_creation_minimal_fields(self, test_user: User) -> None:
        """Тест создания курса только с обязательными полями."""
        course = Course.objects.create(
            owner=test_user,
            title="Django REST Framework",
            description="Курс по DRF",
        )

        assert course.id is not None  # type: ignore[attr-defined]
        assert course.title == "Django REST Framework"
        assert course.description == "Курс по DRF"
        assert not course.preview

    def test_course_str_method(self, test_user: User) -> None:
        """Тест строкового представления курса."""
        course = Course.objects.create(
            owner=test_user, title="FastAPI для продвинутых", description="Современный асинхронный веб"
        )

        assert str(course) == "FastAPI для продвинутых"

    def test_course_has_timestamps(self, test_user: User) -> None:
        """Тест наличия временных меток из BaseModel."""
        course = Course.objects.create(owner=test_user, title="Test Course", description="Test Description")

        assert hasattr(course, "created_at")
        assert hasattr(course, "updated_at")
        assert course.created_at is not None
        assert course.updated_at is not None


@pytest.mark.django_db
class TestLessonModel:
    """Тесты для модели Lesson."""

    def test_lesson_creation_with_all_fields(self, test_user: User) -> None:
        """Тест создания урока со всеми полями."""
        course = Course.objects.create(owner=test_user, title="Python Basics", description="Learn Python")

        preview_image = SimpleUploadedFile(
            name="lesson_preview.jpg", content=b"lesson_content", content_type="image/jpeg"
        )

        lesson = Lesson.objects.create(
            owner=test_user,
            course=course,
            title="Введение в Python",
            description="Первый урок курса",
            preview=preview_image,
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )

        assert lesson.id is not None  # type: ignore[attr-defined]
        assert lesson.course == course
        assert lesson.title == "Введение в Python"
        assert lesson.description == "Первый урок курса"
        assert "lesson_preview" in lesson.preview.name
        assert lesson.preview.name.endswith(".jpg")
        assert lesson.video_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert lesson.created_at is not None
        assert lesson.updated_at is not None

    def test_lesson_creation_minimal_fields(self, test_user: User) -> None:
        """Тест создания урока только с обязательными полями."""
        course = Course.objects.create(owner=test_user, title="Django Course", description="Learn Django")

        lesson = Lesson.objects.create(
            owner=test_user,
            course=course,
            title="Модели Django",
            description="Работа с моделями",
            video_url="https://youtube.com/watch?v=example",
        )

        assert lesson.id is not None  # type: ignore[attr-defined]
        assert lesson.course == course
        assert lesson.title == "Модели Django"
        assert not lesson.preview

    def test_lesson_str_method(self, test_user: User) -> None:
        """Тест строкового представления урока."""
        course = Course.objects.create(owner=test_user, title="Test Course", description="Test")
        lesson = Lesson.objects.create(
            owner=test_user,
            course=course,
            title="Урок 1: Основы",
            description="Первый урок",
            video_url="https://youtube.com/test",
        )

        assert str(lesson) == "Урок 1: Основы"

    def test_lesson_belongs_to_course(self, test_user: User) -> None:
        """Тест связи урока с курсом."""
        course = Course.objects.create(owner=test_user, title="Python Advanced", description="Advanced Python")

        lesson1 = Lesson.objects.create(
            owner=test_user, course=course, title="Lesson 1", description="First", video_url="https://youtube.com/1"
        )
        lesson2 = Lesson.objects.create(
            owner=test_user, course=course, title="Lesson 2", description="Second", video_url="https://youtube.com/2"
        )

        assert lesson1.course == course
        assert lesson2.course == course
        assert course.lessons.count() == 2  # type: ignore[attr-defined]
        assert list(course.lessons.all()) == [lesson1, lesson2]  # type: ignore[attr-defined]

    def test_lesson_cascade_delete(self, test_user: User) -> None:
        """Тест каскадного удаления уроков при удалении курса."""
        course = Course.objects.create(owner=test_user, title="Temporary Course", description="Will be deleted")

        lesson1 = Lesson.objects.create(
            owner=test_user, course=course, title="Lesson 1", description="First", video_url="https://youtube.com/1"
        )
        lesson2 = Lesson.objects.create(
            owner=test_user, course=course, title="Lesson 2", description="Second", video_url="https://youtube.com/2"
        )

        lesson1_id = lesson1.id  # type: ignore[attr-defined]
        lesson2_id = lesson2.id  # type: ignore[attr-defined]

        assert Lesson.objects.filter(course=course).count() == 2

        course.delete()

        assert not Lesson.objects.filter(id=lesson1_id).exists()
        assert not Lesson.objects.filter(id=lesson2_id).exists()
