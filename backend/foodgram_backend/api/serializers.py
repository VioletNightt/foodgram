import base64
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer
from django.core.files.base import ContentFile
from rest_framework import serializers
from recipes.models import Tag, Ingredient, Recipe, RecipeIngredient
from users.models import User
from django.contrib.auth.tokens import default_token_generator


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserSerializer(UserSerializer):

    email = serializers.EmailField(
        required=True,
        max_length=100
    )
    username = serializers.CharField(
        required=True,
        max_length=100
    )

    avatar = Base64ImageField(required=False, allow_null=True)
    image_url = serializers.SerializerMethodField(
        'get_image_url',
        read_only=True,
    )

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password', 'avatar', 'image_url')

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


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

    image = Base64ImageField(required=False, allow_null=True)
    ingredients = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Ingredient.objects.all(),
        many=True
    )
    tags = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Tag.objects.all(),
        many=True
    )
    image_url = serializers.SerializerMethodField(
        'get_image_url',
        read_only=True,
    )

    class Meta:
        model = Recipe
        fields = ('name', 'image', 'text',
                  'ingredients', 'tags', 'cooking_time', 'author', 'image_url')
        read_only_fields = ('author',)

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)

        recipe.ingredients.set(ingredients)
        recipe.tags.set(tags)

        return recipe
