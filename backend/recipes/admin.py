from django.contrib.admin import ModelAdmin, register

from .models import (Favorite, Follow, Ingredient, Recipe, RecipeIngredient,
                     RecipeTag, ShoppingCart, Tag)


@register(Ingredient)
class IngredientAdmin(ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('^name', 'name')
    list_filter = ('measurement_unit',)
    ordering = ('name',)


@register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorites_count', 'cooking_time')
    list_filter = ('author', 'tags')
    search_fields = ('name', 'author__username')

    def favorites_count(self, obj):
        return obj.favorites.count()


@register(RecipeIngredient)
class RecipeIngredientAdmin(ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_filter = ('recipe', 'ingredient')
    autocomplete_fields = ('recipe', 'ingredient')
    search_fields = ('recipe__name', 'ingredient__name')


@register(RecipeTag)
class RecipeTagAdmin(ModelAdmin):
    list_display = ('id', 'recipe', 'tag')
    list_filter = ('tag',)
    autocomplete_fields = ('recipe', 'tag')
    search_fields = ('recipe__name', 'tag__name')


@register(Favorite)
class FavoriteAdmin(ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('user', 'recipe')
    autocomplete_fields = ('user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')


@register(ShoppingCart)
class ShoppingCartAdmin(ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('user', 'recipe')
    autocomplete_fields = ('user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')


@register(Follow)
class FollowAdmin(ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_filter = ('user', 'author')
    autocomplete_fields = ('user', 'author')
    search_fields = ('user__username', 'user__email',
                     'author__username', 'author__email')
