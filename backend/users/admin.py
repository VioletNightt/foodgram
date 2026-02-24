from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin

from .models import User


@register(User)
class MyUserAdmin(UserAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name',
                    'password')
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
