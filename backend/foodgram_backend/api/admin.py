from django.contrib import admin

from recipes.models import Recipe, Ingredient, Tag
from users.models import User

admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(Tag)
admin.site.register(User)
