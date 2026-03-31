import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from djoser.serializers import UserSerializer

from recipes.models import (Follow, Ingredient, Recipe,
                            RecipeIngredient, Tag, Favorite, ShoppingCart)
from users.models import User


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для перевода картинки в base64"""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


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


class ReadRecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингридиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для создания ингридиентов в рецепте."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(),
                                            source='ingredient')
    amount = serializers.IntegerField()

    @staticmethod
    def validate_amount(value):
        """Метод валидации количества"""

        if value < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть больше 0'
            )
        return value

    class Meta:
        """Мета-параметры сериализатора"""

        model = RecipeIngredient
        fields = ('id', 'amount')


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецептов"""
    image = Base64ImageField(use_url=True, required=True)
    ingredients = ReadRecipeIngredientSerializer(
        source='recipe_ingredient', many=True
    )
    tags = TagSerializer(many=True)
    author = UserSerializer()
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
        return bool(
            request
            and request.user.is_authenticated
            and obj.favorites.filter(user=request.user).exists()

        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and obj.shopping_carts.filter(user=request.user).exists()
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов"""
    image = Base64ImageField(use_url=True, required=True)
    ingredients = RecipeIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text',
            'ingredients', 'tags', 'cooking_time',
            'author', 'is_favorited',
            'is_in_shopping_cart'
        )

    def to_representation(self, instance):

        serializer = ReadRecipeSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        )
        return serializer.data

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

    def create_ingredients(recipe, ingredients_data):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            )
            for item in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredient')
        tags_data = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('recipe_ingredient')
        instance = super().update(instance, validated_data)

        instance.tags.set(tags_data)

        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.create_ingredients(instance, ingredients_data)

        return instance


class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор для рецептов в подписках"""
    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ReadFollowSerializer(UserSerializer):
    """Сериализатор для отображения подписок."""

    recipes = serializers.SerializerMethodField(
        method_name='get_recipes')
    recipes_count = serializers.SerializerMethodField(
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
            try:
                limit = int(limit)
                if limit > 0:
                    recipes = recipes[:limit]
            except ValueError:
                pass
        return RecipeShortSerializer(recipes, many=True,
                                     context={'request': request}).data

    @staticmethod
    def get_recipes_count(obj):

        return obj.recipes.count()


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписок."""

    class Meta:

        model = Follow
        fields = ('user', 'author')

    def validate(self, data):

        user = self.data.get('user')
        author = self.data.get('author')

        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя'
            )
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого автора'
            )

        return data

    def to_representation(self, instance):
        serializer = ReadFollowSerializer(
            instance.author,
            context={
                'request': self.context.get('request')
            }
        )
        return serializer.data


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True, use_url=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar')
        instance.save(update_fields=['avatar'])
        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в избранном')
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в корзине')
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
