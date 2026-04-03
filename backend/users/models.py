from django.contrib.auth.models import AbstractUser
from django.db import models

from api.consts import USERNAMES_MAX_LENGTH, EMAIL_MAX_LENGTH


class User(AbstractUser):
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        verbose_name='Email'
    )
    avatar = models.ImageField(
        upload_to='users/images',
        blank=True,
        verbose_name='Аватар'
    )
    first_name = models.CharField(
        max_length=USERNAMES_MAX_LENGTH,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=USERNAMES_MAX_LENGTH,
        verbose_name='Фамилия',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('last_name', 'first_name', 'username')

    def __str__(self):
        return self.username
