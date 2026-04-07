from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import mixins, permissions, status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from users.models import User
from foodgram_backend.settings import DOMAIN
from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from api.serializers import (FavoriteSerializer, ShoppingCartSerializer,
                             UserSerializer, FollowSerializer,
                             IngredientSerializer, RecipeSerializer,
                             TagSerializer, ReadFollowSerializer,
                             AvatarSerializer
                             )
from .filters import IngredientFilter, RecipeFilter
from .pagination import RecipesPagination
from .permissions import IsAuthorOrAuthenticatedOrReadOnly


class UserActionsViewSet(UserViewSet):
    """ViewSet для пользователя"""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = RecipesPagination

    @action(detail=False, methods=('get',),
            permission_classes=(permissions.IsAuthenticated,))
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(detail=False, methods=('get',),
            permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request):
        """Получить список подписок текущего пользователя"""
        authors = User.objects.filter(followers__user=request.user)

        page = self.paginate_queryset(authors)
        serializer = ReadFollowSerializer(page, many=True,
                                          context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=('post',),
            permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)

        data = {'user': request.user.id, 'author': author.id}
        serializer = FollowSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id):
        author = get_object_or_404(User, id=id)

        deleted, _ = Follow.objects.filter(
            user=request.user, author=author).delete()
        if not deleted:
            raise serializers.ValidationError(
                {'errors': ['Вы не подписаны на этого автора.']})
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('put',), url_path='me/avatar',
            permission_classes=(permissions.IsAuthenticated,))
    def avatar(self, request):
        user = request.user
        serializer = AvatarSerializer(user, data=request.data,
                                      context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        if not user.avatar:
            raise serializers.ValidationError(
                {'error': ['У пользователя нет аватара']})
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для ингридиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('^name',)
    permission_classes = (permissions.AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов"""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filterset_class = RecipeFilter
    pagination_class = RecipesPagination
    permission_classes = (IsAuthorOrAuthenticatedOrReadOnly,)

    @action(detail=True, methods=('post',),
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        data = {'user': request.user.id, 'recipe': recipe.id}
        serializer = FavoriteSerializer(data=data,
                                        context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        deleted, _ = Favorite.objects.filter(user=request.user,
                                             recipe=recipe).delete()
        if not deleted:
            raise serializers.ValidationError(
                {'errors': ['Рецепт не в избранном']})
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('post',),
            permission_classes=(permissions.IsAuthenticated,))
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        data = {'user': request.user.id, 'recipe': recipe.id}
        serializer = ShoppingCartSerializer(data=data,
                                            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        deleted, _ = ShoppingCart.objects.filter(user=request.user,
                                                 recipe=recipe).delete()
        if not deleted:
            raise serializers.ValidationError(
                {'errors': ['Рецепт не в корзине']})
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('get',),
            permission_classes=(permissions.IsAuthenticated,),
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """Скачивает файл со списком покупок."""

        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total=Sum('amount')
        ).order_by('ingredient__name').distinct()
        shopping_list = ''
        for ingredient in ingredients:
            shopping_list += (
                f"{ingredient['ingredient__name']} - "
                f"{ingredient['total']} "
                f"({ingredient['ingredient__measurement_unit']})\n"
            )
        return HttpResponse(shopping_list, content_type='text/plain')

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipe, id=pk)
        short_url = f'https://{DOMAIN}/s/{recipe.short_code}/'
        return Response({'short-link': short_url}, status=status.HTTP_200_OK)


def short_link_redirect(request, short_code):
    recipe = get_object_or_404(Recipe, short_code=short_code)
    return redirect(f'/recipes/{recipe.id}/')
