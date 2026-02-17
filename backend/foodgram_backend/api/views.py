from django.db import IntegrityError
from api.serializers import (
    TagSerializer, IngredientSerializer,
    RecipeSerializer, CustomUserSerializer
)
from recipes.models import Favorite, ShoppingCart
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from recipes.models import Tag, Ingredient, Recipe
from users.models import User


class CustomUserViewSet(UserViewSet):
    """ViewSet для регистрации пользователя"""

    serializer_class = CustomUserSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    """ViewSet для ингридиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов"""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            try:
                Favorite.objects.create(user=request.user, recipe=recipe)
            except Exception:
                return Response(
                    {"errors": ["Рецепт уже в избранном."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        deleted_count, _ = Favorite.objects.filter(user=request.user,
                                                   recipe=recipe).delete()
        if deleted_count == 0:
            return Response(
                {"errors": ["Рецепт не в избранном."]},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            try:
                ShoppingCart.objects.create(user=request.user, recipe=recipe)
            except Exception:
                return Response(
                    {"errors": ["Рецепт уже в списке покупок."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            deleted_count, _ = ShoppingCart.objects.filter(
                user=request.user, recipe=recipe).delete()
            if deleted_count == 0:
                return Response(
                    {"errors": ["Рецепта нет в списке покупок."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)