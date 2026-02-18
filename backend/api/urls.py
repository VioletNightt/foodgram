from django.urls import include, path
from rest_framework import routers

from api.views import (RecipeViewSet, TagViewSet,
                       IngredientViewSet, CustomUserViewSet)


router_v1 = routers.DefaultRouter()
router_v1.register('recipes', RecipeViewSet, basename='recipe')
router_v1.register('tags', TagViewSet, basename='tag')
router_v1.register('ingredients', IngredientViewSet, basename='ingredient')
router_v1.register('users', CustomUserViewSet, basename='users')


urlpatterns = [
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    
]
