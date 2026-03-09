"""Пагинаторы для LMS API."""

from rest_framework.pagination import PageNumberPagination


class LMSPaginator(PageNumberPagination):
    """
    Пагинатор для списков курсов и уроков.

    Параметры:
    - page_size: количество элементов на странице (по умолчанию 10)
    - page_size_query_param: параметр запроса для изменения размера страницы
    - max_page_size: максимальный размер страницы для защиты от перегрузки (100)
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
