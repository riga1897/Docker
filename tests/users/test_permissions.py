"""Тесты для кастомных permissions."""

import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIRequestFactory

from lms.models import Course
from users.models import User
from users.permissions import (
    IsModerator,
    IsModeratorOrOwner,
    IsNotModerator,
    IsOwner,
    IsOwnerOrReadOnly,
    IsSelf,
)


@pytest.fixture
def moderator_group(db: None) -> Group:
    """Создать группу модераторов."""
    return Group.objects.create(name="Модераторы")


@pytest.fixture
def moderator_user(db: None, moderator_group: Group) -> User:
    """Создать пользователя-модератора."""
    user = User.objects.create_user(email="moderator@test.com", password="testpass")
    user.groups.add(moderator_group)
    return user


@pytest.fixture
def request_factory() -> APIRequestFactory:
    """Фабрика для создания запросов."""
    return APIRequestFactory()


@pytest.mark.django_db
class TestIsModerator:
    """Тесты для permission IsModerator."""

    def test_moderator_has_permission(self, request_factory: APIRequestFactory, moderator_user: User) -> None:
        """Модератор имеет доступ."""
        request = request_factory.get("/")
        request.user = moderator_user

        permission = IsModerator()
        assert permission.has_permission(request, None) is True

    def test_regular_user_no_permission(self, request_factory: APIRequestFactory, user: User) -> None:
        """Обычный пользователь не имеет доступа."""
        request = request_factory.get("/")
        request.user = user

        permission = IsModerator()
        assert permission.has_permission(request, None) is False

    def test_anonymous_user_no_permission(self, request_factory: APIRequestFactory) -> None:
        """Анонимный пользователь не имеет доступа."""
        from django.contrib.auth.models import AnonymousUser

        request = request_factory.get("/")
        request.user = AnonymousUser()

        permission = IsModerator()
        assert permission.has_permission(request, None) is False


@pytest.mark.django_db
class TestIsOwner:
    """Тесты для permission IsOwner."""

    def test_owner_has_permission(self, request_factory: APIRequestFactory, user: User, course: Course) -> None:
        """Владелец объекта имеет доступ."""
        course.owner = user
        course.save()

        request = request_factory.get("/")
        request.user = user

        permission = IsOwner()
        assert permission.has_object_permission(request, None, course) is True

    def test_non_owner_no_permission(
        self, request_factory: APIRequestFactory, user: User, another_user: User, course: Course
    ) -> None:
        """Не владелец не имеет доступа."""
        course.owner = another_user
        course.save()

        request = request_factory.get("/")
        request.user = user

        permission = IsOwner()
        assert permission.has_object_permission(request, None, course) is False

    def test_anonymous_user_no_permission(self, request_factory: APIRequestFactory, course: Course) -> None:
        """Анонимный пользователь не имеет доступа."""
        from django.contrib.auth.models import AnonymousUser

        request = request_factory.get("/")
        request.user = AnonymousUser()

        permission = IsOwner()
        assert permission.has_object_permission(request, None, course) is False


@pytest.mark.django_db
class TestIsOwnerOrReadOnly:
    """Тесты для permission IsOwnerOrReadOnly."""

    def test_safe_methods_authenticated_user(
        self, request_factory: APIRequestFactory, user: User, course: Course
    ) -> None:
        """Аутентифицированный пользователь может читать."""
        request = request_factory.get("/")
        request.user = user

        permission = IsOwnerOrReadOnly()
        assert permission.has_object_permission(request, None, course) is True

    def test_safe_methods_anonymous_user(self, request_factory: APIRequestFactory, course: Course) -> None:
        """Анонимный пользователь не может читать."""
        from django.contrib.auth.models import AnonymousUser

        request = request_factory.get("/")
        request.user = AnonymousUser()

        permission = IsOwnerOrReadOnly()
        assert permission.has_object_permission(request, None, course) is False

    def test_write_methods_owner(self, request_factory: APIRequestFactory, user: User, course: Course) -> None:
        """Владелец может изменять."""
        course.owner = user
        course.save()

        request = request_factory.post("/")
        request.user = user

        permission = IsOwnerOrReadOnly()
        assert permission.has_object_permission(request, None, course) is True

    def test_write_methods_non_owner(
        self, request_factory: APIRequestFactory, user: User, another_user: User, course: Course
    ) -> None:
        """Не владелец не может изменять."""
        course.owner = another_user
        course.save()

        request = request_factory.post("/")
        request.user = user

        permission = IsOwnerOrReadOnly()
        assert permission.has_object_permission(request, None, course) is False

    def test_write_methods_anonymous_user(self, request_factory: APIRequestFactory, course: Course) -> None:
        """Анонимный пользователь не может изменять."""
        from django.contrib.auth.models import AnonymousUser

        request = request_factory.post("/")
        request.user = AnonymousUser()

        permission = IsOwnerOrReadOnly()
        assert permission.has_object_permission(request, None, course) is False


@pytest.mark.django_db
class TestIsModeratorOrOwner:
    """Тесты для permission IsModeratorOrOwner."""

    def test_moderator_has_permission(
        self, request_factory: APIRequestFactory, moderator_user: User, course: Course, another_user: User
    ) -> None:
        """Модератор имеет доступ к чужим объектам."""
        course.owner = another_user
        course.save()

        request = request_factory.get("/")
        request.user = moderator_user

        permission = IsModeratorOrOwner()
        assert permission.has_object_permission(request, None, course) is True

    def test_owner_has_permission(self, request_factory: APIRequestFactory, user: User, course: Course) -> None:
        """Владелец имеет доступ к своим объектам."""
        course.owner = user
        course.save()

        request = request_factory.get("/")
        request.user = user

        permission = IsModeratorOrOwner()
        assert permission.has_object_permission(request, None, course) is True

    def test_non_owner_no_permission(
        self, request_factory: APIRequestFactory, user: User, another_user: User, course: Course
    ) -> None:
        """Обычный пользователь не имеет доступа к чужим объектам."""
        course.owner = another_user
        course.save()

        request = request_factory.get("/")
        request.user = user

        permission = IsModeratorOrOwner()
        assert permission.has_object_permission(request, None, course) is False

    def test_anonymous_user_no_permission(self, request_factory: APIRequestFactory, course: Course) -> None:
        """Анонимный пользователь не имеет доступа."""
        from django.contrib.auth.models import AnonymousUser

        request = request_factory.get("/")
        request.user = AnonymousUser()

        permission = IsModeratorOrOwner()
        assert permission.has_object_permission(request, None, course) is False


@pytest.mark.django_db
class TestIsNotModerator:
    """Тесты для permission IsNotModerator."""

    def test_regular_user_has_permission(self, request_factory: APIRequestFactory, user: User) -> None:
        """Обычный пользователь имеет доступ."""
        request = request_factory.get("/")
        request.user = user

        permission = IsNotModerator()
        assert permission.has_permission(request, None) is True

    def test_moderator_no_permission(self, request_factory: APIRequestFactory, moderator_user: User) -> None:
        """Модератор не имеет доступа."""
        request = request_factory.get("/")
        request.user = moderator_user

        permission = IsNotModerator()
        assert permission.has_permission(request, None) is False

    def test_anonymous_user_no_permission(self, request_factory: APIRequestFactory) -> None:
        """Анонимный пользователь не имеет доступа."""
        from django.contrib.auth.models import AnonymousUser

        request = request_factory.get("/")
        request.user = AnonymousUser()

        permission = IsNotModerator()
        assert permission.has_permission(request, None) is False


@pytest.mark.django_db
class TestIsSelf:
    """Тесты для permission IsSelf."""

    def test_user_edits_own_profile(self, request_factory: APIRequestFactory, user: User) -> None:
        """Пользователь может редактировать свой профиль."""
        request = request_factory.put("/")
        request.user = user

        permission = IsSelf()
        assert permission.has_object_permission(request, None, user) is True

    def test_user_edits_other_profile(
        self, request_factory: APIRequestFactory, user: User, another_user: User
    ) -> None:
        """Пользователь не может редактировать чужой профиль."""
        request = request_factory.put("/")
        request.user = user

        permission = IsSelf()
        assert permission.has_object_permission(request, None, another_user) is False

    def test_anonymous_user_no_permission(self, request_factory: APIRequestFactory, user: User) -> None:
        """Анонимный пользователь не может редактировать профиль."""
        from django.contrib.auth.models import AnonymousUser

        request = request_factory.put("/")
        request.user = AnonymousUser()

        permission = IsSelf()
        assert permission.has_object_permission(request, None, user) is False
