from django.db import IntegrityError
from api.serializers import (
    TagSerializer, IngredientSerializer,
    RecipeSerializer, CustomUserSerializer, SubscriptionSerializer
)
from recipes.models import Favorite, ShoppingCart
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from recipes.models import Tag, Ingredient, Recipe
from users.models import User, Subscription


class CustomUserViewSet(UserViewSet):
    """ViewSet для пользователя"""

    serializer_class = CustomUserSerializer

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, id=None):
        user_to_subscribe_to = get_object_or_404(User, id=id)

        if request.user == user_to_subscribe_to:
            return Response(
                {"errors": ["Нельзя подписаться на самого себя."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            try:
                subscription = Subscription.objects.create(
                    subscriber=request.user,
                    subscribed_to=user_to_subscribe_to
                )
                serializer = self.get_serializer(user_to_subscribe_to)
                # Используем CustomUserSerializer для возврата информации о пользователе
                # Но нам нужен формат, как в примере ответа API для /subscribe/
                # Поэтому используем SubscriptionSerializer, но ему нужно передать объект Subscription
                # Лучше создать отдельный метод или переиспользовать SubscriptionSerializer
                # Но SubscriptionSerializer ожидает объект Subscription, а не User
                # Создадим временный объект или используем альтернативный подход

                # Альтернативный подход: создать временный экземпляр Subscription
                # и использовать его в SubscriptionSerializer
                temp_sub = Subscription(subscriber=request.user, subscribed_to=user_to_subscribe_to)
                # Но это не сохранено в БД. Serialization не должен зависеть от несохранённых объектов.
                # Лучше передать контекст и сформировать данные вручную или использовать другой сериализатор.

                # Самый чистый способ - использовать SubscriptionSerializer, передав ему объект Subscription
                # Для этого нужно получить или создать объект Subscription
                subscription_instance = get_object_or_404(Subscription, subscriber=request.user, subscribed_to=user_to_subscribe_to)
                serializer = SubscriptionSerializer(subscription_instance, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(
                    {"errors": ["Вы уже подписаны на этого пользователя."]},
                    status=status.HTTP_400_BAD_REQUEST
                )

        elif request.method == 'DELETE':
            deleted_count, _ = Subscription.objects.filter(
                subscriber=request.user,
                subscribed_to=user_to_subscribe_to
            ).delete()
            if deleted_count == 0:
                return Response(
                    {"errors": ["Вы не подписаны на этого пользователя."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated],
            url_path='subscriptions')
    def subscriptions(self, request):
        """
        Возвращает список подписок текущего пользователя.
        """
        user = request.user
        subscriptions_qs = Subscription.objects.filter(subscriber=user).select_related('subscribed_to__avatar')

        # Пагинация
        page_number = request.query_params.get('page')
        limit = request.query_params.get('limit')
        recipes_limit = request.query_params.get('recipes_limit')

        paginator = Paginator(subscriptions_qs, limit or 6) # 6 по умолчанию
        page_obj = paginator.get_page(page_number)

        serializer = SubscriptionSerializer(page_obj, many=True, context={'request': request, 'recipes_limit': recipes_limit})
        return Response({
            "count": paginator.count,
            "next": page_obj.has_next() and page_obj.next_page_number() or None,
            "previous": page_obj.has_previous() and page_obj.previous_page_number() or None,
            "results": serializer.data
        })


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