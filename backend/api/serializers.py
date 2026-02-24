import base64

from django.core.files.base import ContentFile
from recipes.models import Follow, Ingredient, Recipe, RecipeIngredient, Tag
from rest_framework import serializers
from users.models import User


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для перевода картинки в base64"""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя"""

    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    email = serializers.EmailField(
        required=True,
        max_length=100
    )
    username = serializers.CharField(
        required=True,
        max_length=100
    )
    avatar = Base64ImageField(required=False, allow_null=True, use_url=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'avatar', 'is_subscribed')
        extra_kwargs = {'password': {'write_only': True}}

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(user=request.user,
                                         author=obj).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингридиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингридиентов в рецепте."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(),
                                            source='ingredient')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецептов"""
    image = Base64ImageField(use_url=True, required=True)
    ingredients = RecipeIngredientSerializer(many=True,
                                             required=True,
                                             source='recipe_ingredient')
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=True
    )
    name = serializers.CharField(required=True, max_length=256)
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(required=True, min_value=1)
    author = CustomUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text',
            'ingredients', 'tags', 'cooking_time',
            'author', 'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.shopping_carts.filter(user=request.user).exists()
        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(
            instance.tags.all(), many=True
        ).data
        return representation

    def validate(self, data):

        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                'Нельзя сделать рецепт без ингридиентов.'
            )
        lst_ingredient = []

        for ingredient in ingredients:
            if ingredient['id'] in lst_ingredient:
                raise serializers.ValidationError(
                    'Ингредиенты должны быть уникальными.'
                )
            lst_ingredient.append(ingredient['id'])

        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Нельзя сделать рецепт без тегов.'
            )
        lst_tags = []
        for tag in tags:
            if tag in lst_tags:
                raise serializers.ValidationError(
                    'Теги должны быть уникальными.'
                )
            lst_tags.append(tag)

        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredient')
        tags_data = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        for item in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.image = validated_data.get('image', instance.image)
        instance.save()

        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
            instance.tags.set(tags_data)

        if 'recipe_ingredient' in validated_data:
            ingredients_data = validated_data.pop('recipe_ingredient')
            RecipeIngredient.objects.filter(recipe=instance).delete()
            for item in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=item['ingredient'],
                    amount=item['amount']
                )

        return instance


class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор для рецептов в подписках"""
    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(CustomUserSerializer):
    """Сериализатор для модели Follow."""

    recipes = serializers.SerializerMethodField(
        read_only=True,
        method_name='get_recipes')
    recipes_count = serializers.SerializerMethodField(
        read_only=True
    )

    class Meta:

        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar',)

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit', None)
        recipes = obj.recipes.all()
        if limit:
            limit = int(limit)
            recipes = recipes[:limit]
        return RecipeShortSerializer(recipes, many=True,
                                     context={'request': request}).data

    @staticmethod
    def get_recipes_count(obj):

        return obj.recipes.count()
