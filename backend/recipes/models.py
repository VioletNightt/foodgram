import random
import string

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from users.models import User
from api.consts import (
    TAG_MAX_LENGTH, INGREDIENT_MAX_LENGTH,
    MEASUREMENT_UNIT_MAX_LENGTH, RECIPE_NAME_MAX_LENGTH,
    MIN_COOKING_TIME, MAX_COOKING_TIME, MIN_AMOUNT, MAX_AMOUNT
)


class Tag(models.Model):
    """Модель тегов """
    name = models.CharField(
        max_length=TAG_MAX_LENGTH,
        unique=True,
        verbose_name='Название')
    slug = models.SlugField(
        max_length=TAG_MAX_LENGTH,
        unique=True,
        verbose_name='Идентификатор')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов"""
    name = models.CharField(max_length=INGREDIENT_MAX_LENGTH,
                            verbose_name='Название')
    measurement_unit = models.CharField(max_length=MEASUREMENT_UNIT_MAX_LENGTH,
                                        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецептов"""

    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='recipes',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=RECIPE_NAME_MAX_LENGTH,
                            verbose_name='Название')
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Картинка'
    )
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(Ingredient,
                                         verbose_name='Ингредиенты',
                                         related_name='recipes')
    tags = models.ManyToManyField(Tag,
                                  verbose_name='Теги',
                                  related_name='recipes',
                                  through='RecipeTag')
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=f'''Время приготовления не может
                 быть меньше {MIN_COOKING_TIME} минуты.'''
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message=f'''Время приготовления не может
                 превышать {MAX_COOKING_TIME} минут.'''
            )
        ],
        verbose_name='Время приготовления'
    )
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='Время создания')
    short_code = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Короткий код'
    )

    def generate_unique_code(self, length=6):
        """Генерирует уникальный код из букв и цифр."""
        while True:
            code = ''.join(random.choices(
                string.ascii_letters + string.digits, k=length))
            if not Recipe.objects.filter(short_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.pk and not self.short_code:
            self.short_code = self.generate_unique_code()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Модель связь рецетов и ингредиентов"""
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               verbose_name='Рецепт',
                               related_name='recipe_ingredient')
    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE,
                                   verbose_name='Ингридиент')
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                MIN_AMOUNT,
                message=f'''Количество ингредиента
                  не может быть меньше {MIN_AMOUNT}.'''
            ),
            MaxValueValidator(
                MAX_AMOUNT,
                message=f'''Количество ингредиента
                  не может превышать {MAX_AMOUNT}.'''
            )
        ],
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        ordering = ('recipe', 'ingredient')

    def __str__(self):
        return f'''{self.ingredient.name} - {self.amount}
         {self.ingredient.measurement_unit} (рецепт: {self.recipe.name})'''


class RecipeTag(models.Model):
    """Модель связь рецептов и тегов"""

    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               verbose_name='Рецепт')
    tag = models.ForeignKey(Tag,
                            on_delete=models.CASCADE,
                            verbose_name='Тег')

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецептов'
        ordering = ('recipe', 'tag')

    def __str__(self):
        return f'{self.recipe.name} - {self.tag.name}'


class Favorite(models.Model):
    """Модель для избранного"""

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='favorites')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='favorites')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_user_recipe'
            )
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'

    def __str__(self):
        return f"{self.user.username} -> {self.recipe.name}"


class ShoppingCart(models.Model):
    """Модель для списка покупок"""

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='shopping_carts')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE,
                               related_name='shopping_carts')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_cart_user_recipe'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        ordering = ('user', 'recipe')

    def __str__(self):
        return f'Корзина {self.user.username}: {self.recipe.name}'


class Follow(models.Model):
    """Модель для подписок"""

    author = models.ForeignKey(User, related_name='followers',
                               on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='following')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_follow_user_author'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('user', 'author')

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
