"""Представления для пользователей."""

from typing import Any

from django.db.models import QuerySet
from django_filters import rest_framework as filters
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from users.models import Payment, User
from users.permissions import IsOwner, IsSelf
from users.serializers import (
    PaymentSerializer,
    PublicUserSerializer,
    RegisterSerializer,
    UserDetailSerializer,
)
from users.services import prepare_stripe_payment_data, refresh_payment_status


@extend_schema(
    tags=["Пользователи"],
    summary="Регистрация нового пользователя",
    description="Создает новый аккаунт пользователя. Доступно без аутентификации.",
    responses={
        status.HTTP_201_CREATED: RegisterSerializer,
        status.HTTP_400_BAD_REQUEST: None,
    },
)
class RegisterView(generics.CreateAPIView):
    """
    Endpoint для регистрации новых пользователей.

    Доступен всем без аутентификации.
    Требует email, password и password_confirm.
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=["Пользователи"])
@extend_schema_view(
    list=extend_schema(
        summary="Список всех пользователей",
        description="Возвращает публичную информацию обо всех пользователях",
    ),
    retrieve=extend_schema(
        summary="Детальная информация о пользователе",
        description="Возвращает публичные данные пользователя, или полные данные если запрашивается свой профиль",
    ),
    create=extend_schema(
        summary="Создание пользователя (используйте /api/register/)",
        description="Не используется для регистрации, используйте /api/register/ вместо этого",
    ),
    update=extend_schema(
        summary="Обновление профиля пользователя",
        description="Пользователь может обновить только свой профиль",
    ),
    partial_update=extend_schema(
        summary="Частичное обновление профиля пользователя",
        description="Пользователь может частично обновить только свой профиль",
    ),
    destroy=extend_schema(
        summary="Удаление профиля пользователя",
        description="Пользователь может удалить только свой профиль",
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями.

    Согласно Дополнительному заданию:
    - list/retrieve: любой пользователь видит публичные данные всех (email, first_name, phone, city, avatar)
    - retrieve (свой профиль): полные данные включая last_name и платежи
    - update/partial_update/destroy: только свой профиль

    Модераторы:
    - Видят публичные профили всех пользователей
    - НЕ могут редактировать/удалять чужие профили
    """

    queryset = User.objects.all()
    lookup_field = "pk"

    def get_serializer_class(self) -> type:
        """Выбор сериализатора: публичный для чужих профилей, детальный для своего."""
        if self.action in ["list"]:
            return PublicUserSerializer
        elif self.action == "retrieve":
            # Если запрашивает свой профиль - полные данные
            if self.kwargs.get(self.lookup_field) and self.request.user and self.get_object() == self.request.user:
                return UserDetailSerializer
            # Чужой профиль - только публичные данные (или схема по умолчанию)
            return PublicUserSerializer
        # create, update, partial_update, destroy - полные данные
        return UserDetailSerializer

    def get_permissions(self) -> list[Any]:
        """Разграничение прав доступа по action."""
        if self.action in ["list", "retrieve"]:
            # Просмотр: все аутентифицированные
            return [permissions.IsAuthenticated()]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Редактирование/удаление: только свой профиль
            # (модераторы тоже могут редактировать СВОИ профили)
            return [permissions.IsAuthenticated(), IsSelf()]
        # create: доступно всем (регистрация через RegisterView)
        return [permissions.AllowAny()]


class PaymentFilter(filters.FilterSet):
    """
    Фильтры для модели Payment.

    Поддерживает фильтрацию по:
    - курсу
    - уроку
    - способу оплаты
    """

    class Meta:  # type: ignore[misc]
        model = Payment
        fields = {
            "course": ["exact"],
            "lesson": ["exact"],
            "payment_method": ["exact"],
        }


@extend_schema(tags=["Платежи"])
@extend_schema_view(
    list=extend_schema(
        summary="Список платежей пользователя",
        description="Возвращает все платежи текущего пользователя с возможностью фильтрации и сортировки",
        parameters=[
            OpenApiParameter(
                name="course",
                description="Фильтр по ID курса",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="lesson",
                description="Фильтр по ID урока",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="payment_method",
                description="Фильтр по способу оплаты (cash/transfer/stripe)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="ordering",
                description="Сортировка по полю (payment_date, amount, -payment_date, -amount)",
                required=False,
                type=str,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Детальная информация о платеже",
        description="Возвращает подробную информацию о конкретном платеже",
    ),
    create=extend_schema(
        summary="Создание нового платежа",
        description=(
            "Создает новый платеж для текущего пользователя. "
            "При указании метода 'stripe' автоматически создается платежная ссылка Stripe."
        ),
    ),
    update=extend_schema(
        summary="Полное обновление платежа",
        description="Обновляет все поля платежа. Доступно только владельцу.",
    ),
    partial_update=extend_schema(
        summary="Частичное обновление платежа",
        description="Обновляет выбранные поля платежа. Доступно только владельцу.",
    ),
    destroy=extend_schema(
        summary="Удаление платежа",
        description="Удаляет платеж. Доступно только владельцу.",
    ),
)
class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для модели Payment.

    Поддерживает CRUD операции и фильтрацию по:
    - курсу (course)
    - уроку (lesson)
    - способу оплаты (payment_method)

    Сортировка доступна по:
    - дате оплаты (payment_date)
    - сумме (amount)

    Права доступа:
    - Пользователь видит и редактирует только свои платежи
    - Создание, редактирование, удаление доступно только владельцу

    Оптимизация: select_related('owner', 'course', 'lesson') предзагружает
    все связанные объекты одним запросом, устраняя проблему N+1.
    """

    queryset = Payment.objects.select_related("owner", "course", "lesson")
    serializer_class = PaymentSerializer
    filterset_class = PaymentFilter
    ordering_fields = ["payment_date", "amount"]
    ordering = ["-payment_date"]

    def get_permissions(self) -> list[Any]:
        """Разграничение прав доступа по action."""
        if self.action in ["list", "create"]:
            # Список и создание: все аутентифицированные
            return [permissions.IsAuthenticated()]
        # retrieve, update, partial_update, destroy: только владелец
        return [permissions.IsAuthenticated(), IsOwner()]

    def get_queryset(self) -> QuerySet[Payment]:
        """
        Фильтрация платежей: пользователь видит только свои платежи.

        Возвращает queryset отфильтрованный по owner = текущий пользователь.
        """
        return super().get_queryset().filter(owner=self.request.user)

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """
        Автоматическая привязка owner при создании платежа через service layer.

        Делегирует Stripe бизнес-логику в prepare_stripe_payment_data() сервис.
        Сохраняет DRF контракт через serializer.save() с дополнительными полями.
        """
        from typing import Any as AnyType

        payment_method = serializer.validated_data.get("payment_method")
        extra_fields: dict[str, AnyType] = {"owner": self.request.user}

        if payment_method == "stripe":
            course = serializer.validated_data.get("course")
            lesson = serializer.validated_data.get("lesson")
            amount = serializer.validated_data.get("amount")

            stripe_data = prepare_stripe_payment_data(amount, course, lesson)
            extra_fields.update(stripe_data)

        serializer.save(**extra_fields)

    @extend_schema(
        summary="Проверить статус оплаты",
        description="Проверяет статус платежа в Stripe (дополнительное задание)",
        responses={
            status.HTTP_200_OK: {
                "type": "object",
                "properties": {
                    "payment_status": {"type": "string", "example": "paid"},
                    "message": {"type": "string", "example": "Платёж успешно завершён"},
                },
            },
            status.HTTP_400_BAD_REQUEST: {
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "Платёж не был создан через Stripe"},
                },
            },
        },
    )
    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated, IsOwner])
    def check_status(self, request: Request, pk: int | None = None) -> Response:
        """
        Проверяет статус платежа в Stripe через service layer.

        Делегирует бизнес-логику в refresh_payment_status() сервис.
        ViewSet только обрабатывает HTTP запрос/ответ.

        Returns:
            Response с информацией о статусе платежа
        """
        payment = self.get_object()

        try:
            result = refresh_payment_status(payment.pk)  # type: ignore[arg-type]
            return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Ошибка при проверке статуса: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
