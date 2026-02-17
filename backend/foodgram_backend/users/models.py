from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        verbose_name='Email'
    )
    avatar = models.ImageField(
        upload_to='users/images',
        blank=True,
        verbose_name='Аватар'
    )
    is_subscribed = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE, 
        related_name='subscriptions',
        verbose_name='Подписчик'
    )
    subscribed_to = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('subscriber', 'subscribed_to')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.subscriber.username} -> {self.subscribed_to.username}'
