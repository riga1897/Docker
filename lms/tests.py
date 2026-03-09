"""Тесты для LMS приложения."""

from typing import Any

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lms.constants import SubscriptionMessages
from lms.models import Course, Lesson, Subscription
from users.models import User


class LessonCRUDTestCase(APITestCase):
    """Тестирование CRUD операций для модели Lesson."""

    def setUp(self) -> None:
        """Подготовка тестовых данных перед каждым тестом."""
        self.user: User = User.objects.create_user(  # type: ignore[misc]
            email="testuser@example.com",
            password="testpass123",
        )
        self.moderator: User = User.objects.create_user(  # type: ignore[misc]
            email="moderator@example.com",
            password="modpass123",
            is_staff=True,
        )
        self.other_user: User = User.objects.create_user(  # type: ignore[misc]
            email="other@example.com",
            password="otherpass123",
        )

        self.course: Course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            owner=self.user,
        )
        self.lesson: Lesson = Lesson.objects.create(
            title="Test Lesson",
            description="Test Lesson Description",
            course=self.course,
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            owner=self.user,
        )

        self.list_url: str = reverse("lms:lesson-list")
        self.detail_url: str = reverse("lms:lesson-detail", kwargs={"pk": self.lesson.pk})

    def test_lesson_list_authenticated(self) -> None:
        """Тест получения списка уроков аутентифицированным пользователем."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

    def test_lesson_list_unauthenticated(self) -> None:
        """Тест получения списка уроков неаутентифицированным пользователем."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lesson_create_authenticated(self) -> None:
        """Тест создания урока аутентифицированным пользователем."""
        self.client.force_authenticate(user=self.user)
        data: dict[str, Any] = {
            "title": "New Lesson",
            "description": "New Description",
            "course": self.course.pk,
            "video_url": "https://www.youtube.com/watch?v=abcdefghijk",
        }
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)
        self.assertEqual(response.data["title"], "New Lesson")
        self.assertEqual(response.data["owner"], self.user.pk)

    def test_lesson_create_moderator_forbidden(self) -> None:
        """Тест запрета создания урока модератором."""
        self.client.force_authenticate(user=self.moderator)
        data: dict[str, Any] = {
            "title": "Moderator Lesson",
            "description": "Description",
            "course": self.course.pk,
            "video_url": "https://www.youtube.com/watch?v=test1234567",
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_retrieve_authenticated(self) -> None:
        """Тест получения деталей урока."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test Lesson")

    def test_lesson_update_owner(self) -> None:
        """Тест обновления урока владельцем."""
        self.client.force_authenticate(user=self.user)
        data: dict[str, Any] = {
            "title": "Updated Lesson",
            "description": "Updated Description",
            "course": self.course.pk,
            "video_url": "https://www.youtube.com/watch?v=updated1234",
        }
        response = self.client.put(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, "Updated Lesson")

    def test_lesson_update_moderator(self) -> None:
        """Тест обновления урока модератором."""
        self.client.force_authenticate(user=self.moderator)
        data: dict[str, Any] = {
            "title": "Moderator Updated",
            "description": "Moderator Description",
            "course": self.course.pk,
            "video_url": "https://www.youtube.com/watch?v=moderator123",
        }
        response = self.client.put(self.detail_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, "Moderator Updated")

    def test_lesson_update_other_user_forbidden(self) -> None:
        """Тест запрета обновления урока другим пользователем."""
        self.client.force_authenticate(user=self.other_user)
        data: dict[str, Any] = {
            "title": "Unauthorized Update",
            "description": "Unauthorized",
            "course": self.course.pk,
            "video_url": "https://www.youtube.com/watch?v=unauthorized",
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_delete_owner(self) -> None:
        """Тест удаления урока владельцем."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 0)

    def test_lesson_delete_moderator_forbidden(self) -> None:
        """Тест запрета удаления урока модератором."""
        self.client.force_authenticate(user=self.moderator)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lesson_invalid_youtube_url(self) -> None:
        """Тест валидации YouTube URL."""
        self.client.force_authenticate(user=self.user)
        data: dict[str, Any] = {
            "title": "Invalid URL Lesson",
            "description": "Invalid",
            "course": self.course.pk,
            "video_url": "https://vimeo.com/123456",
        }
        response = self.client.post(self.list_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("video_url", response.data)


class SubscriptionTestCase(APITestCase):
    """Тестирование системы подписок на курсы."""

    def setUp(self) -> None:
        """Подготовка тестовых данных."""
        self.user: User = User.objects.create_user(  # type: ignore[misc]
            email="subscriber@example.com",
            password="subpass123",
        )
        self.course: Course = Course.objects.create(
            title="Subscription Course",
            description="Course for subscriptions",
            owner=self.user,
        )
        self.subscription_url: str = reverse("lms:subscription")

    def test_subscribe_to_course(self) -> None:
        """Тест подписки на курс."""
        self.client.force_authenticate(user=self.user)
        data: dict[str, Any] = {"course_id": self.course.pk}
        response = self.client.post(self.subscription_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], SubscriptionMessages.ADDED)
        self.assertTrue(Subscription.objects.filter(user=self.user, course=self.course).exists())

    def test_unsubscribe_from_course(self) -> None:
        """Тест отписки от курса."""
        Subscription.objects.create(user=self.user, course=self.course)
        self.client.force_authenticate(user=self.user)
        data: dict[str, Any] = {"course_id": self.course.pk}
        response = self.client.post(self.subscription_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], SubscriptionMessages.REMOVED)
        self.assertFalse(Subscription.objects.filter(user=self.user, course=self.course).exists())

    def test_subscription_toggle_idempotent(self) -> None:
        """Тест toggle подписки (subscribe -> unsubscribe -> subscribe)."""
        self.client.force_authenticate(user=self.user)
        data: dict[str, Any] = {"course_id": self.course.pk}

        response1 = self.client.post(self.subscription_url, data)
        self.assertEqual(response1.data["message"], SubscriptionMessages.ADDED)

        response2 = self.client.post(self.subscription_url, data)
        self.assertEqual(response2.data["message"], SubscriptionMessages.REMOVED)

        response3 = self.client.post(self.subscription_url, data)
        self.assertEqual(response3.data["message"], SubscriptionMessages.ADDED)

    def test_subscription_unauthenticated(self) -> None:
        """Тест запрета подписки неаутентифицированному пользователю."""
        data: dict[str, Any] = {"course_id": self.course.pk}
        response = self.client.post(self.subscription_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_is_subscribed_field_in_course_list(self) -> None:
        """Тест поля is_subscribed в списке курсов."""
        Subscription.objects.create(user=self.user, course=self.course)
        self.client.force_authenticate(user=self.user)

        url = reverse("lms:course-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        courses = response.data["results"]
        self.assertTrue(courses[0]["is_subscribed"])

    def test_is_subscribed_field_false_when_not_subscribed(self) -> None:
        """Тест поля is_subscribed=False когда нет подписки."""
        self.client.force_authenticate(user=self.user)

        url = reverse("lms:course-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        courses = response.data["results"]
        self.assertFalse(courses[0]["is_subscribed"])

    def test_is_subscribed_unauthenticated_user(self) -> None:
        """Тест поля is_subscribed=False для неаутентифицированного пользователя."""
        from rest_framework.test import APIRequestFactory

        from lms.serializers import CourseSerializer

        factory = APIRequestFactory()
        request = factory.get("/")
        serializer = CourseSerializer(self.course, context={"request": request})

        self.assertFalse(serializer.data["is_subscribed"])


class CoursePermissionsTestCase(APITestCase):
    """Тестирование прав доступа для курсов."""

    def setUp(self) -> None:
        """Подготовка тестовых данных."""
        self.owner: User = User.objects.create_user(  # type: ignore[misc]
            email="owner@example.com",
            password="ownerpass",
        )
        self.moderator: User = User.objects.create_user(  # type: ignore[misc]
            email="mod@example.com",
            password="modpass",
            is_staff=True,
        )
        self.other_user: User = User.objects.create_user(  # type: ignore[misc]
            email="other@example.com",
            password="otherpass",
        )

        self.course: Course = Course.objects.create(
            title="Permissions Course",
            description="Testing permissions",
            owner=self.owner,
        )

        self.list_url: str = reverse("lms:course-list")
        self.detail_url: str = reverse("lms:course-detail", kwargs={"pk": self.course.pk})

    def test_course_create_owner(self) -> None:
        """Тест создания курса владельцем."""
        self.client.force_authenticate(user=self.owner)
        data: dict[str, Any] = {
            "title": "New Course",
            "description": "New Description",
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_course_create_moderator_forbidden(self) -> None:
        """Тест запрета создания курса модератором."""
        self.client.force_authenticate(user=self.moderator)
        data: dict[str, Any] = {
            "title": "Moderator Course",
            "description": "Forbidden",
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_course_update_owner(self) -> None:
        """Тест обновления курса владельцем."""
        self.client.force_authenticate(user=self.owner)
        data: dict[str, Any] = {
            "title": "Updated by Owner",
            "description": "Owner update",
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_course_update_moderator(self) -> None:
        """Тест обновления курса модератором."""
        self.client.force_authenticate(user=self.moderator)
        data: dict[str, Any] = {
            "title": "Updated by Moderator",
            "description": "Moderator update",
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_course_update_other_user_forbidden(self) -> None:
        """Тест запрета обновления курса другим пользователем."""
        self.client.force_authenticate(user=self.other_user)
        data: dict[str, Any] = {
            "title": "Unauthorized",
            "description": "Forbidden",
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_course_delete_owner(self) -> None:
        """Тест удаления курса владельцем."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_course_delete_moderator_forbidden(self) -> None:
        """Тест запрета удаления курса модератором."""
        self.client.force_authenticate(user=self.moderator)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PaginationTestCase(APITestCase):
    """Тестирование пагинации для курсов и уроков."""

    def setUp(self) -> None:
        """Подготовка тестовых данных."""
        self.user: User = User.objects.create_user(  # type: ignore[misc]
            email="paginator@example.com",
            password="paginpass",
        )

        for i in range(15):
            Course.objects.create(
                title=f"Course {i}",
                description=f"Description {i}",
                owner=self.user,
            )

        self.course: Course = Course.objects.first()  # type: ignore[assignment]
        for i in range(15):
            Lesson.objects.create(
                title=f"Lesson {i}",
                description=f"Lesson Description {i}",
                course=self.course,
                video_url=f"https://www.youtube.com/watch?v=test{i:07d}",
                owner=self.user,
            )

    def test_course_pagination_default_page_size(self) -> None:
        """Тест пагинации курсов с размером страницы по умолчанию (10)."""
        self.client.force_authenticate(user=self.user)
        url = reverse("lms:course-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)

    def test_lesson_pagination_custom_page_size(self) -> None:
        """Тест пагинации уроков с кастомным размером страницы."""
        self.client.force_authenticate(user=self.user)
        url = reverse("lms:lesson-list") + "?page_size=5"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)

    def test_pagination_second_page(self) -> None:
        """Тест получения второй страницы."""
        self.client.force_authenticate(user=self.user)
        url = reverse("lms:course-list") + "?page=2"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)

    def test_pagination_max_page_size_limit(self) -> None:
        """Тест ограничения максимального размера страницы (max_page_size=100)."""
        self.client.force_authenticate(user=self.user)
        url = reverse("lms:course-list") + "?page_size=200"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data["results"]), 100)


class ModelStringRepresentationTestCase(APITestCase):
    """Тестирование строковых представлений моделей (__str__ методов)."""

    def setUp(self) -> None:
        """Подготовка тестовых данных перед каждым тестом."""
        self.user: User = User.objects.create_user(  # type: ignore[misc]
            email="testuser@example.com",
            password="testpass123",
        )
        self.course: Course = Course.objects.create(
            title="Python Programming",
            description="Learn Python",
            owner=self.user,
        )
        self.lesson: Lesson = Lesson.objects.create(
            title="Introduction to Python",
            description="First lesson",
            course=self.course,
            video_url="https://www.youtube.com/watch?v=test123",
            owner=self.user,
        )
        self.subscription: Subscription = Subscription.objects.create(
            user=self.user,
            course=self.course,
        )

    def test_course_str_representation(self) -> None:
        """Тест строкового представления модели Course."""
        self.assertEqual(str(self.course), "Python Programming")

    def test_lesson_str_representation(self) -> None:
        """Тест строкового представления модели Lesson."""
        self.assertEqual(str(self.lesson), "Introduction to Python")

    def test_subscription_str_representation(self) -> None:
        """Тест строкового представления модели Subscription."""
        expected = f"{self.user} подписан на {self.course}"
        self.assertEqual(str(self.subscription), expected)


class ValidatorTestCase(APITestCase):
    """Тестирование валидаторов LMS приложения."""

    @staticmethod
    def test_youtube_validator_none_value() -> None:
        """Тест валидатора YouTube URL с None значением."""
        from lms.validators import validate_youtube_url

        validate_youtube_url(None)

    @staticmethod
    def test_youtube_validator_empty_string() -> None:
        """Тест валидатора YouTube URL с пустой строкой."""
        from lms.validators import validate_youtube_url

        validate_youtube_url("")

    @staticmethod
    def test_youtube_validator_valid_url() -> None:
        """Тест валидатора YouTube URL с корректной ссылкой."""
        from lms.validators import validate_youtube_url

        validate_youtube_url("https://www.youtube.com/watch?v=test123")

    def test_youtube_validator_invalid_url(self) -> None:
        """Тест валидатора YouTube URL с некорректной ссылкой."""
        from rest_framework.serializers import ValidationError

        from lms.validators import validate_youtube_url

        with self.assertRaises(ValidationError):
            validate_youtube_url("https://vimeo.com/123456")
