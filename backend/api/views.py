from api.serializers import (CustomUserSerializer, FollowSerializer,
                             IngredientSerializer, RecipeSerializer,
                             RecipeShortSerializer, TagSerializer)
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from foodgram_backend.settings import DOMAIN
from recipes.models import (Favorite, Follow, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Tag)
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import User

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import IsAuthorOrReadOnly


class CustomUserViewSet(UserViewSet):
    """ViewSet для пользователя"""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'],)
    def me(self, request):
        user = request.user
        serializer = CustomUserSerializer(user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        """Получить список подписок текущего пользователя"""
        authors = User.objects.filter(followers__user=request.user)

        page = self.paginate_queryset(authors)
        serializer = FollowSerializer(page, many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True, methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,))
    def subscribe(self, request, id):

        user = request.user
        author = get_object_or_404(User, id=id)
        if user == author:
            return Response(
                {"errors": ["Нельзя подписаться на самого себя"]},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            follow, created = Follow.objects.get_or_create(
                user=user, author=author)
            if not created:
                return Response(
                    {"errors": ["Вы уже подписаны на этого автора."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = FollowSerializer(author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        deleted_count, _ = Follow.objects.filter(user=user,
                                                 author=author).delete()
        if deleted_count == 0:
            return Response(
                {"errors": ["Вы не были подписаны на автора."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=('put', 'delete'), url_path='me/avatar',
            permission_classes=[permissions.IsAuthenticated])
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = CustomUserSerializer(user,
                                              data=request.data,
                                              partial=True,
                                              context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({'avatar': serializer.data.get('avatar')},
                                status=status.HTTP_200_OK)
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        if not user.avatar:
            return Response({"error": "У пользователя нет аватара"},
                            status=status.HTTP_400_BAD_REQUEST)
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """ViewSet для ингридиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    search_fields = ('^name',)
    permission_classes = (permissions.AllowAny,)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        ingredients = sorted(queryset, key=lambda x: x.name.lower())
        serializer = self.get_serializer(ingredients, many=True)
        return Response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов"""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filterset_class = RecipeFilter
    pagination_class = CustomPagination
    permission_classes = (IsAuthorOrReadOnly,)

    @action(detail=True, methods=('post', 'delete'),
            permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                return Response(
                    {"errors": ["Рецепт уже в избранном."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeShortSerializer(recipe,
                                               context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        deleted_count, _ = Favorite.objects.filter(user=request.user,
                                                   recipe=recipe).delete()
        if deleted_count == 0:
            return Response(
                {"errors": ["Рецепт не в избранном."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(recipe, context={'request': request})
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        if request.method == 'POST':
            cart_item, created = ShoppingCart.objects.get_or_create(
                user=user, recipe=recipe)
            if not created:
                return Response(
                    {"errors": ["Рецепт уже в списке покупок."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeShortSerializer(recipe,
                                               context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            deleted_count, _ = ShoppingCart.objects.filter(
                user=request.user, recipe=recipe).delete()
            if deleted_count == 0:
                return Response(
                    {"errors": ["Рецепта нет в списке покупок."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.get_serializer(recipe,
                                             context={'request': request})
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """Скачивает файл со списком покупок."""

        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum=Sum('amount'))
        shopping_list = ''
        for ingredient in ingredients:
            shopping_list += (
                f"{ingredient['ingredient__name']} - "
                f"{ingredient['sum']}"
                f"({ingredient['ingredient__measurement_unit']})\n"
            )
        return HttpResponse(shopping_list, content_type='text/plain')

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipe, id=pk)
        return Response(
            {'short-link': f'https://{DOMAIN}/recipes/{recipe.id}'},
            status=status.HTTP_200_OK)
