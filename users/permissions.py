"""
Кастомные разрешения для LMS приложения.

Классы:
- IsModerator: Проверка принадлежности к группе "Модераторы"
- IsOwner: Проверка что пользователь является владельцем объекта
- IsOwnerOrReadOnly: Чтение доступно всем, изменение только владельцу
- IsModeratorOrOwner: Модератор или владелец объекта (для редактирования)
- IsNotModerator: Не модератор (для создания курсов/уроков)
- IsSelf: Пользователь редактирует сам себя (для UserViewSet)
"""

from typing import Any

from rest_framework import permissions
from rest_framework.request import Request


class IsModerator(permissions.BasePermission):
    """
    Разрешение для модераторов.

    Проверяет принадлежность пользователя к группе "Модераторы" или флаг is_staff.
    Модераторы имеют расширенные права на просмотр и редактирование контента.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        """Проверка прав на уровне запроса."""
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(
            request.user.is_staff or request.user.groups.filter(name="Модераторы").exists()  # type: ignore[attr-defined]
        )


class IsOwner(permissions.BasePermission):
    """
    Разрешение для владельца объекта.

    Проверяет что текущий пользователь является владельцем объекта (owner).
    Применяется на уровне объекта.
    """

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Проверка прав на уровне объекта."""
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(obj, "owner") and obj.owner == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение: чтение всем, изменение только владельцу.

    - GET, HEAD, OPTIONS: доступны всем аутентифицированным пользователям
    - POST, PUT, PATCH, DELETE: доступны только владельцу объекта
    """

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Проверка прав на уровне объекта."""
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)

        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(obj, "owner") and obj.owner == request.user


class IsModeratorOrOwner(permissions.BasePermission):
    """
    Разрешение: модератор ИЛИ владелец объекта.

    Модератор (is_staff или группа "Модераторы") может редактировать любые объекты.
    Владелец может редактировать свои объекты.
    Используется для update/partial_update actions.
    """

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Проверка прав на уровне объекта."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Модератор может редактировать любые объекты
        if request.user.is_staff or request.user.groups.filter(name="Модераторы").exists():  # type: ignore[attr-defined]
            return True

        # Владелец может редактировать свой объект
        return hasattr(obj, "owner") and obj.owner == request.user


class IsNotModerator(permissions.BasePermission):
    """
    Разрешение: НЕ модератор.

    Модераторы (is_staff или группа "Модераторы") не могут создавать курсы/уроки (согласно Заданию 2).
    Используется для create action.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        """Проверка прав на уровне запроса."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Модераторы НЕ могут создавать
        return not (
            request.user.is_staff or request.user.groups.filter(name="Модераторы").exists()  # type: ignore[attr-defined]
        )


class IsSelf(permissions.BasePermission):
    """
    Разрешение: пользователь редактирует сам себя.

    Проверяет что текущий пользователь и объект User - одно лицо.
    Используется для UserViewSet (update/partial_update/destroy).
    """

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        """Проверка прав на уровне объекта."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Пользователь может редактировать только свой профиль
        return obj == request.user
