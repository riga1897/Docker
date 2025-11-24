"""Представления для корневого API."""

from typing import Any

from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.reverse import reverse


@extend_schema(
    summary="API Root",
    description="Главная страница API со списком всех доступных ресурсов и документации",
    tags=["API"],
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name="ApiRootResponse",
                fields={
                    "course": serializers.URLField(),
                    "user": serializers.URLField(),
                    "payment": serializers.URLField(),
                    "lesson": serializers.URLField(),
                    "register": serializers.URLField(),
                    "auth": serializers.DictField(),
                    "documentation": serializers.DictField(),
                },
            ),
            description="Словарь со ссылками на все доступные эндпоинты API",
        )
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request: Request, response_format: str | None = None) -> Response:
    """
    Корневой эндпоинт API со списком всех доступных ресурсов.

    Динамически собирает все endpoints из роутеров приложений lms и users.
    При добавлении нового ViewSet в любое приложение, он автоматически появится здесь.

    Принцип работы:
    1. Импортируем роутеры из lms.urls и users.urls
    2. Проходим по router.registry (список зарегистрированных ViewSet-ов)
    3. Для каждого ViewSet создаём ссылку через reverse()
    4. Для Generic Views (lesson) добавляем вручную, так как они не в роутере

    Args:
        request: HTTP запрос
        response_format: Формат ответа (json, html и т.д.)

    Returns:
        Response: Словарь со ссылками на все доступные эндпоинты

    Пример результата:
        {
            "course": "http://example.com/api/courses/",
            "user": "http://example.com/api/users/",
            "payment": "http://example.com/api/payments/",
            "lesson": "http://example.com/api/lessons/"
        }
    """
    from lms.urls import router as lms_router
    from users.urls import router as users_router

    endpoints: dict[str, Any] = {}

    # Автоматически собираем endpoints из роутера LMS приложения
    for _prefix, _viewset, basename in lms_router.registry:
        endpoints[basename] = reverse(f"lms:{basename}-list", request=request, format=response_format)

    # Автоматически собираем endpoints из роутера Users приложения
    for _prefix, _viewset, basename in users_router.registry:
        endpoints[basename] = reverse(f"users:{basename}-list", request=request, format=response_format)

    # Добавляем Generic Views вручную (lesson использует Generic Views, а не ViewSet)
    endpoints["lesson"] = reverse("lms:lesson-list", request=request, format=response_format)

    # Добавляем endpoint регистрации
    endpoints["register"] = reverse("users:register", request=request, format=response_format)

    # Добавляем JWT аутентификацию endpoints
    endpoints["auth"] = {
        "obtain_token": reverse("token_obtain_pair", request=request, format=response_format),
        "refresh_token": reverse("token_refresh", request=request, format=response_format),
        "verify_token": reverse("token_verify", request=request, format=response_format),
    }

    # Добавляем документацию API
    endpoints["documentation"] = {
        "swagger-ui": reverse("swagger-ui", request=request, format=response_format),
        "redoc": reverse("redoc", request=request, format=response_format),
        "openapi-schema": reverse("schema", request=request, format=response_format),
    }

    return Response(endpoints)
