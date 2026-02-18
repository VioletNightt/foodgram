import django_filters
from django_filters.rest_framework import FilterSet

from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
    """ Фильтр для отображения избранного и списка покупок"""
    tags = django_filters.filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug')
    is_favorited = django_filters.filters.NumberFilter(
        method='is_in_favorites_filter')
    is_in_shopping_cart = django_filters.filters.NumberFilter(
        method='is_in_shoppingcart_filter')

    def is_in_favorites_filter(self, queryset, name, value):
        if value == 1:
            user = self.request.user
            return queryset.filter(favorites__user_id=user.id)
        return queryset

    def is_in_shoppingcart_filter(self, queryset, name, value):
        if value == 1:
            user = self.request.user
            return queryset.filter(shopping_recipe__user_id=user.id)
        return queryset

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')