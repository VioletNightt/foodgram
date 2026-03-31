from rest_framework.pagination import PageNumberPagination

from .consts import PAGE_SIZE


class RecipesPagination(PageNumberPagination):
    """Кастомный пагинатор для вывода 6 элементов на странице."""

    page_size_query_param = 'limit'
    page_size = PAGE_SIZE
