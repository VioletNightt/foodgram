from django.contrib.auth.models import AbstractUser
from django.db import models


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
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя',
        blank=False,
        null=False
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия',
        blank=False,
        null=False
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.username
