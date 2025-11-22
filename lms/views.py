"""Views для LMS API."""

from typing import TYPE_CHECKING, Any, cast

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics, permissions, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from lms.models import Course, Lesson
from lms.paginators import LMSPaginator
from lms.serializers import CourseSerializer, LessonSerializer
from users.permissions import IsModeratorOrOwner, IsNotModerator, IsOwner

if TYPE_CHECKING:
    from users.models import User


@extend_schema(tags=["Курсы"])
@extend_schema_view(
    list=extend_schema(
        summary="Список всех курсов",
        description="Возвращает список всех курсов с информацией о количестве уроков и статусе подписки",
        parameters=[
            OpenApiParameter(
                name="page",
                description="Номер страницы для пагинации",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="page_size",
                description="Количество элементов на странице (по умолчанию 10, максимум 100)",
                required=False,
                type=int,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Детальная информация о курсе",
        description="Возвращает подробную информацию о курсе, включая список уроков",
    ),
    create=extend_schema(
        summary="Создание нового курса",
        description="Создает новый курс. Недоступно модераторам.",
    ),
    update=extend_schema(
        summary="Полное обновление курса",
        description="Обновляет все поля курса. Доступно владельцу или модератору.",
    ),
    partial_update=extend_schema(
        summary="Частичное обновление курса",
        description="Обновляет выбранные поля курса. Доступно владельцу или модератору.",
    ),
    destroy=extend_schema(
        summary="Удаление курса",
        description="Удаляет курс. Доступно только владельцу.",
    ),
)
class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet для модели Course.

    Предоставляет CRUD операции согласно Заданию 2 и 3:
    - list: GET /courses/ - доступно всем аутентифицированным
    - create: POST /courses/ - доступно всем аутентифицированным (кроме модераторов)
    - retrieve: GET /courses/{id}/ - доступно всем аутентифицированным
    - update: PUT /courses/{id}/ - владелец ИЛИ модератор
    - partial_update: PATCH /courses/{id}/ - владелец ИЛИ модератор
    - destroy: DELETE /courses/{id}/ - только владелец

    Оптимизация: prefetch_related('lessons', 'subscribers') и select_related('owner')
    предзагружают уроки, подписки и владельца, устраняя проблему N+1.
    """

    queryset = Course.objects.prefetch_related("lessons", "subscribers").select_related("owner")
    serializer_class = CourseSerializer
    pagination_class = LMSPaginator

    def get_permissions(self) -> list[Any]:
        """Разграничение прав доступа по action согласно заданию."""
        if self.action == "create":
            # Создание: всем аутентифицированным, кроме модераторов
            return [permissions.IsAuthenticated(), IsNotModerator()]
        elif self.action == "destroy":
            # Удаление: только владелец
            return [permissions.IsAuthenticated(), IsOwner()]
        elif self.action in ["update", "partial_update"]:
            # Редактирование: владелец ИЛИ модератор
            return [permissions.IsAuthenticated(), IsModeratorOrOwner()]
        # list, retrieve: всем аутентифицированным
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Автоматическая привязка owner при создании."""
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer: BaseSerializer[Any]) -> None:
        """
        Обновление курса с асинхронной отправкой уведомлений подписчикам.

        После сохранения изменений запускает Celery задачу для отправки email
        уведомлений подписчикам курса (если прошло 4 часа с последнего уведомления).
        """
        instance = serializer.save()

        # Запускаем асинхронную задачу отправки email
        from lms.tasks import send_course_update_notification

        send_course_update_notification.delay(instance.id)  # type: ignore[attr-defined]


@extend_schema(
    tags=["Уроки"],
    responses={status.HTTP_200_OK: LessonSerializer(many=True)},
)
@extend_schema_view(
    get=extend_schema(
        summary="Список всех уроков",
        description="Возвращает список всех уроков с пагинацией",
        parameters=[
            OpenApiParameter(
                name="page",
                description="Номер страницы для пагинации",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="page_size",
                description="Количество элементов на странице (по умолчанию 10, максимум 100)",
                required=False,
                type=int,
            ),
        ],
    ),
    post=extend_schema(
        summary="Создание нового урока",
        description="Создает новый урок. Недоступно модераторам.",
    ),
)
class LessonListCreateAPIView(generics.ListCreateAPIView):
    """
    Generic view для списка уроков и создания нового урока.

    Согласно Заданию 2:
    - GET /lessons/ - доступно всем аутентифицированным
    - POST /lessons/ - доступно всем аутентифицированным (кроме модераторов)

    Оптимизация: select_related('course', 'owner') загружает
    связанный курс и владельца одним JOIN запросом.
    """

    queryset = Lesson.objects.select_related("course", "owner")
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsNotModerator]
    pagination_class = LMSPaginator

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Автоматическая привязка owner при создании."""
        serializer.save(owner=self.request.user)


@extend_schema(tags=["Уроки"])
@extend_schema_view(
    get=extend_schema(
        summary="Детальная информация об уроке",
        description="Возвращает подробную информацию об уроке",
    ),
    put=extend_schema(
        summary="Полное обновление урока",
        description="Обновляет все поля урока. Доступно владельцу или модератору.",
    ),
    patch=extend_schema(
        summary="Частичное обновление урока",
        description="Обновляет выбранные поля урока. Доступно владельцу или модератору.",
    ),
    delete=extend_schema(
        summary="Удаление урока",
        description="Удаляет урок. Доступно только владельцу.",
    ),
)
class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Generic view для получения, обновления и удаления урока.

    Согласно Заданию 2 и 3:
    - GET /lessons/{id}/ - доступно всем аутентифицированным
    - PUT /lessons/{id}/ - владелец ИЛИ модератор
    - PATCH /lessons/{id}/ - владелец ИЛИ модератор
    - DELETE /lessons/{id}/ - только владелец

    Оптимизация: select_related('course', 'owner') загружает
    связанный курс и владельца одним JOIN запросом.
    """

    queryset = Lesson.objects.select_related("course", "owner")
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsModeratorOrOwner]

    def get_permissions(self) -> list[Any]:
        """Разграничение прав доступа: удаление только владельцу."""
        if self.request.method == "DELETE":
            return [permissions.IsAuthenticated(), IsOwner()]
        return [permissions.IsAuthenticated(), IsModeratorOrOwner()]


@extend_schema(
    tags=["Подписки"],
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "course_id": {
                    "type": "integer",
                    "description": "ID курса для подписки/отписки",
                }
            },
            "required": ["course_id"],
        }
    },
    responses={
        status.HTTP_200_OK: {
            "type": "object",
            "properties": {"message": {"type": "string", "example": "подписка добавлена"}},
        }
    },
    summary="Управление подпиской на курс",
    description="Переключает подписку на курс: если подписка существует - удаляет, если нет - создает",
)
class SubscriptionAPIView(APIView):
    """
    API endpoint для управления подписками на курсы.

    POST: Toggle подписки - если подписка существует, удаляет её,
    если не существует - создаёт новую.

    Требуется аутентификация.
    """

    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def post(request: Request, *_args: Any, **_kwargs: Any) -> Response:
        """
        Toggle подписки на курс через service layer.

        Делегирует бизнес-логику в toggle_subscription() сервис.
        View только обрабатывает HTTP запрос/ответ.

        Ожидает в request.data:
        - course_id: ID курса

        Returns:
            Response с message:
            - 'подписка добавлена' - если подписка создана
            - 'подписка удалена' - если подписка удалена
        """
        from lms.services import toggle_subscription

        user = cast("User", request.user)
        course_id = request.data.get("course_id")
        course = get_object_or_404(Course, pk=course_id)

        _is_subscribed, message = toggle_subscription(user, course)

        return Response({"message": message})
