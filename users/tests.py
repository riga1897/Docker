"""Тесты для users приложения."""

from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from lms.models import Course, Lesson
from users.models import Payment, User


class UserManagerTestCase(APITestCase):
    """Тестирование UserManager."""

    def test_create_user_without_email(self) -> None:
        """Тест создания пользователя без email."""
        with self.assertRaises(ValueError) as context:
            User.objects.create_user(email="", password="testpass123")  # type: ignore[misc]
        self.assertEqual(str(context.exception), "Email обязателен")

    def test_create_superuser_success(self) -> None:
        """Тест успешного создания суперпользователя."""
        superuser: User = User.objects.create_superuser(  # type: ignore[misc]
            email="admin@example.com",
            password="adminpass123",
        )
        self.assertTrue(superuser.is_staff)  # type: ignore[attr-defined]
        self.assertTrue(superuser.is_superuser)  # type: ignore[attr-defined]

    def test_create_superuser_invalid_is_staff(self) -> None:
        """Тест создания суперпользователя с is_staff=False."""
        with self.assertRaises(ValueError) as context:
            User.objects.create_superuser(  # type: ignore[misc]
                email="admin@example.com",
                password="adminpass123",
                is_staff=False,
            )
        self.assertEqual(str(context.exception), "Суперпользователь должен иметь is_staff=True")

    def test_create_superuser_invalid_is_superuser(self) -> None:
        """Тест создания суперпользователя с is_superuser=False."""
        with self.assertRaises(ValueError) as context:
            User.objects.create_superuser(  # type: ignore[misc]
                email="admin@example.com",
                password="adminpass123",
                is_superuser=False,
            )
        self.assertEqual(str(context.exception), "Суперпользователь должен иметь is_superuser=True")


class PaymentModelTestCase(APITestCase):
    """Тестирование модели Payment."""

    def setUp(self) -> None:
        """Подготовка тестовых данных."""
        self.user: User = User.objects.create_user(  # type: ignore[misc]
            email="testuser@example.com",
            password="testpass123",
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
            video_url="https://www.youtube.com/watch?v=test123",
            owner=self.user,
        )

    def test_payment_str_with_course(self) -> None:
        """Тест строкового представления платежа за курс."""
        payment = Payment.objects.create(
            owner=self.user,
            course=self.course,
            amount=Decimal("1000.00"),
            payment_method="cash",
        )
        expected = f"Платёж {self.user.email} - {self.course.title} - 1000.00₽"  # type: ignore[attr-defined]
        self.assertEqual(str(payment), expected)

    def test_payment_str_with_lesson(self) -> None:
        """Тест строкового представления платежа за урок."""
        payment = Payment.objects.create(
            owner=self.user,
            lesson=self.lesson,
            amount=Decimal("500.00"),
            payment_method="transfer",
        )
        expected = f"Платёж {self.user.email} - {self.lesson.title} - 500.00₽"  # type: ignore[attr-defined]
        self.assertEqual(str(payment), expected)

    def test_payment_str_without_course_and_lesson(self) -> None:
        """Тест строкового представления платежа без курса и урока."""
        payment = Payment(
            owner=self.user,
            amount=Decimal("100.00"),
            payment_method="cash",
        )
        expected = f"Платёж {self.user.email} - Неизвестно - 100.00₽"  # type: ignore[attr-defined]
        self.assertEqual(str(payment), expected)

    def test_payment_clean_validation_no_course_no_lesson(self) -> None:
        """Тест валидации платежа без курса и урока."""
        payment = Payment(
            owner=self.user,
            amount=Decimal("100.00"),
            payment_method="cash",
        )
        with self.assertRaises(ValidationError) as context:
            payment.clean()
        self.assertIn("Должен быть указан либо курс, либо урок для оплаты", str(context.exception))


class PaymentViewSetTestCase(APITestCase):
    """Тестирование PaymentViewSet."""

    def setUp(self) -> None:
        """Подготовка тестовых данных."""
        self.user: User = User.objects.create_user(  # type: ignore[misc]
            email="testuser@example.com",
            password="testpass123",
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
        self.payment: Payment = Payment.objects.create(
            owner=self.user,
            course=self.course,
            amount=Decimal("1000.00"),
            payment_method="cash",
        )
        self.list_url: str = reverse("users:payment-list")
        self.detail_url: str = reverse("users:payment-detail", kwargs={"pk": self.payment.pk})

    def test_payment_list_authenticated(self) -> None:
        """Тест получения списка платежей аутентифицированным пользователем."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_payment_list_unauthenticated(self) -> None:
        """Тест запрета доступа к списку платежей неаутентифицированному пользователю."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_payment_create(self) -> None:
        """Тест создания платежа."""
        self.client.force_authenticate(user=self.user)
        data: dict[str, Any] = {
            "owner": self.user.pk,
            "course": self.course.pk,
            "amount": "500.00",
            "payment_method": "transfer",
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 2)

    def test_payment_retrieve_owner(self) -> None:
        """Тест получения платежа владельцем."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_payment_update_owner(self) -> None:
        """Тест обновления платежа владельцем."""
        self.client.force_authenticate(user=self.user)
        data: dict[str, Any] = {
            "owner": self.user.pk,
            "course": self.course.pk,
            "amount": "1500.00",
            "payment_method": "cash",
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.amount, Decimal("1500.00"))

    def test_payment_update_other_user_forbidden(self) -> None:
        """Тест запрета обновления чужого платежа."""
        self.client.force_authenticate(user=self.other_user)
        data: dict[str, Any] = {
            "owner": self.user.pk,
            "course": self.course.pk,
            "amount": "2000.00",
            "payment_method": "cash",
        }
        response = self.client.put(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_payment_delete_owner(self) -> None:
        """Тест удаления платежа владельцем."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Payment.objects.count(), 0)


class UserViewSetTestCase(APITestCase):
    """Тестирование UserViewSet."""

    def setUp(self) -> None:
        """Подготовка тестовых данных."""
        self.user: User = User.objects.create_user(  # type: ignore[misc]
            email="testuser@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.other_user: User = User.objects.create_user(  # type: ignore[misc]
            email="other@example.com",
            password="otherpass123",
            first_name="Other",
            last_name="User",
        )
        self.list_url: str = reverse("users:user-list")
        self.detail_url: str = reverse("users:user-detail", kwargs={"pk": self.user.pk})
        self.other_detail_url: str = reverse("users:user-detail", kwargs={"pk": self.other_user.pk})

    def test_user_list_authenticated(self) -> None:
        """Тест получения списка пользователей."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_list_unauthenticated(self) -> None:
        """Тест запрета доступа к списку пользователей неаутентифицированному пользователю."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_retrieve_self_full_data(self) -> None:
        """Тест получения полных данных своего профиля."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("last_name", response.data)
        self.assertIn("payments", response.data)

    def test_user_retrieve_other_public_data(self) -> None:
        """Тест получения публичных данных чужого профиля."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("last_name", response.data)
        self.assertNotIn("payments", response.data)

    def test_user_update_self(self) -> None:
        """Тест обновления своего профиля."""
        self.client.force_authenticate(user=self.user)
        data: dict[str, Any] = {
            "email": "testuser@example.com",
            "first_name": "Updated",
            "last_name": "User",
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")  # type: ignore[attr-defined]

    def test_user_update_other_forbidden(self) -> None:
        """Тест запрета обновления чужого профиля."""
        self.client.force_authenticate(user=self.user)
        data: dict[str, Any] = {
            "email": "other@example.com",
            "first_name": "Hacked",
        }
        response = self.client.patch(self.other_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_delete_self(self) -> None:
        """Тест удаления своего профиля."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_delete_other_forbidden(self) -> None:
        """Тест запрета удаления чужого профиля."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class RegisterViewTestCase(APITestCase):
    """Тестирование RegisterView."""

    def setUp(self) -> None:
        """Подготовка тестовых данных."""
        self.url: str = reverse("users:register")

    def test_register_success(self) -> None:
        """Тест успешной регистрации пользователя."""
        data: dict[str, Any] = {
            "email": "newuser@example.com",
            "password": "newpass123",
            "password_confirm": "newpass123",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_register_password_mismatch(self) -> None:
        """Тест регистрации с несовпадающими паролями."""
        data: dict[str, Any] = {
            "email": "newuser@example.com",
            "password": "newpass123",
            "password_confirm": "differentpass",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ApiRootTestCase(APITestCase):
    """Тестирование корневого API эндпоинта."""

    def test_api_root(self) -> None:
        """Тест корневого API эндпоинта."""
        url = reverse("api-root")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("course", response.data)
        self.assertIn("lesson", response.data)
        self.assertIn("user", response.data)
        self.assertIn("payment", response.data)
        self.assertIn("register", response.data)
        self.assertIn("auth", response.data)


class PermissionsEdgeCasesTestCase(APITestCase):
    """Тестирование edge cases кастомных пермишнов."""

    def setUp(self) -> None:
        """Подготовка тестовых данных."""
        from django.contrib.auth.models import AnonymousUser

        self.user: User = User.objects.create_user(  # type: ignore[misc]
            email="testuser@example.com",
            password="testpass123",
        )
        self.course: Course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            owner=self.user,
        )
        self.anonymous_user = AnonymousUser()

    @staticmethod
    def _create_mock_request(user: Any, method: str = "GET") -> Any:
        """Создание простого mock request объекта."""
        from dataclasses import dataclass

        @dataclass
        class MockRequest:
            user: Any
            method: str

        return MockRequest(user, method)

    def test_isowner_unauthenticated(self) -> None:
        """Тест IsOwner для неаутентифицированного пользователя."""
        from users.permissions import IsOwner

        permission = IsOwner()
        request = self._create_mock_request(self.anonymous_user)
        self.assertFalse(permission.has_object_permission(request, None, self.course))

    def test_isself_unauthenticated(self) -> None:
        """Тест IsSelf для неаутентифицированного пользователя."""
        from users.permissions import IsSelf

        permission = IsSelf()
        request = self._create_mock_request(self.anonymous_user)
        self.assertFalse(permission.has_object_permission(request, None, self.user))

    def test_ismoderator_unauthenticated(self) -> None:
        """Тест IsModerator для неаутентифицированного пользователя."""
        from users.permissions import IsModerator

        permission = IsModerator()
        request = self._create_mock_request(self.anonymous_user)
        self.assertFalse(permission.has_permission(request, None))

    def test_isnotmoderator_unauthenticated(self) -> None:
        """Тест IsNotModerator для неаутентифицированного пользователя."""
        from users.permissions import IsNotModerator

        permission = IsNotModerator()
        request = self._create_mock_request(self.anonymous_user)
        self.assertFalse(permission.has_permission(request, None))

    def test_isownerorreadonly_unauthenticated_safe_method(self) -> None:
        """Тест IsOwnerOrReadOnly для неаутентифицированного пользователя (GET)."""
        from users.permissions import IsOwnerOrReadOnly

        permission = IsOwnerOrReadOnly()
        request = self._create_mock_request(self.anonymous_user, method="GET")
        self.assertFalse(permission.has_object_permission(request, None, self.course))

    def test_isownerorreadonly_unauthenticated_unsafe_method(self) -> None:
        """Тест IsOwnerOrReadOnly для неаутентифицированного пользователя (POST)."""
        from users.permissions import IsOwnerOrReadOnly

        permission = IsOwnerOrReadOnly()
        request = self._create_mock_request(self.anonymous_user, method="POST")
        self.assertFalse(permission.has_object_permission(request, None, self.course))

    def test_ismoderatororoowner_unauthenticated(self) -> None:
        """Тест IsModeratorOrOwner для неаутентифицированного пользователя."""
        from users.permissions import IsModeratorOrOwner

        permission = IsModeratorOrOwner()
        request = self._create_mock_request(self.anonymous_user)
        self.assertFalse(permission.has_object_permission(request, None, self.course))


class SerializerEdgeCasesTestCase(APITestCase):
    """Тестирование edge cases сериализаторов."""

    def setUp(self) -> None:
        """Подготовка тестовых данных."""
        self.user: User = User.objects.create_user(  # type: ignore[misc]
            email="testuser@example.com",
            password="testpass123",
        )
        self.course: Course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            owner=self.user,
        )

    def test_payment_serializer_validation_empty(self) -> None:
        """Тест валидации PaymentSerializer без курса и урока."""
        from users.serializers import PaymentSerializer

        data: dict[str, Any] = {
            "owner": self.user.pk,
            "amount": "100.00",
            "payment_method": "cash",
        }
        serializer = PaymentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_user_detail_serializer_create_without_password(self) -> None:
        """Тест создания пользователя через UserDetailSerializer без пароля."""
        from users.serializers import UserDetailSerializer

        data: dict[str, Any] = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
        }
        serializer = UserDetailSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.email, "newuser@example.com")

    def test_user_detail_serializer_update_without_password(self) -> None:
        """Тест обновления пользователя через UserDetailSerializer без изменения пароля."""
        from users.serializers import UserDetailSerializer

        data: dict[str, Any] = {
            "email": "testuser@example.com",
            "first_name": "Updated",
        }
        serializer = UserDetailSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.first_name, "Updated")

    def test_user_detail_serializer_create_with_password(self) -> None:
        """Тест создания пользователя через UserDetailSerializer с паролем."""
        from users.serializers import UserDetailSerializer

        data: dict[str, Any] = {
            "email": "userWithPass@example.com",
            "first_name": "User",
            "last_name": "WithPassword",
            "password": "securepass123",
        }
        serializer = UserDetailSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertTrue(user.check_password("securepass123"))

    def test_user_detail_serializer_update_with_password(self) -> None:
        """Тест обновления пользователя через UserDetailSerializer с изменением пароля."""
        from users.serializers import UserDetailSerializer

        data: dict[str, Any] = {
            "email": "testuser@example.com",
            "first_name": "Updated",
            "password": "newpassword123",
        }
        serializer = UserDetailSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertTrue(user.check_password("newpassword123"))


class UserViewSetCreateTestCase(APITestCase):
    """Тестирование создания пользователя через UserViewSet (action='create')."""

    def test_user_create_via_viewset(self) -> None:
        """Тест создания пользователя через UserViewSet.create (покрывает AllowAny permission)."""
        url = reverse("users:user-list")
        data = {
            "email": "newuser@example.com",
            "password": "newpass123",
            "first_name": "New",
            "last_name": "User",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())


class PaymentCheckStatusTestCase(APITestCase):
    """Тестирование custom action check_status для проверки статуса Stripe платежа."""

    def setUp(self) -> None:
        """Подготовка тестовых данных."""
        self.user: User = User.objects.create_user(  # type: ignore[misc]
            email="testuser@example.com",
            password="testpass123",
        )
        self.course: Course = Course.objects.create(
            title="Test Course",
            description="Test Description",
            owner=self.user,
        )

    def test_check_status_non_stripe_payment(self) -> None:
        """Тест проверки статуса для платежа НЕ через Stripe."""
        payment = Payment.objects.create(
            owner=self.user,
            course=self.course,
            amount=Decimal("100.00"),
            payment_method="cash",
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("users:payment-detail", kwargs={"pk": payment.pk}) + "check_status/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Платёж не был создан через Stripe")

    def test_check_status_stripe_payment_no_session_id(self) -> None:
        """Тест проверки статуса Stripe платежа без session_id."""
        payment = Payment.objects.create(
            owner=self.user,
            course=self.course,
            amount=Decimal("100.00"),
            payment_method="stripe",
            stripe_session_id=None,
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("users:payment-detail", kwargs={"pk": payment.pk}) + "check_status/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
