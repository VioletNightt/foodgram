from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from rest_framework import serializers
from recipes.models import Tag, Ingredient, Recipe
from users.models import User
from django.contrib.auth.tokens import default_token_generator


class CustomUserSerializer(UserSerializer):

    email = serializers.EmailField(
        required=True,
        max_length=100
    )
    username = serializers.CharField(
        required=True,
        max_length=100
    )

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = ('name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингридиентов."""

    class Meta:
        model = Ingredient
        fields = ('name', 'measurement_unit')


class RecipeSerizlizer(serializers.ModelSerializer):
    """Сериализатор рецептов"""

    class Meta:
        model = Recipe
        fields = ('name', 'image', 'text',
                  'ingredients', 'tags', 'cooking_time')
