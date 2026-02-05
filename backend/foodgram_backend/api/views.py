from api.serializers import (
    TagSerializer, IngredientSerializer,
    RecipeSerizlizer, CustomUserSerializer
)
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from recipes.models import Tag, Ingredient, Recipe
from users.models import User


class CustomUserViewSet(UserViewSet):
    """ViewSet для регистрации пользователя"""

    serializer_class = CustomUserSerializer


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ModelViewSet):
    """ViewSet для ингридиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов"""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerizlizer
