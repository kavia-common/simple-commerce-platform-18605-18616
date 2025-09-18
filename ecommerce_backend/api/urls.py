from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    health,
    CategoryViewSet,
    ProductViewSet,
    get_cart,
    cart_add_item,
    cart_remove_item,
    cart_update_item,
    cart_clear,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'products', ProductViewSet, basename='products')

urlpatterns = [
    # PUBLIC_INTERFACE
    path('health/', health, name='Health'),

    # DRF ViewSets
    path('', include(router.urls)),

    # PUBLIC_INTERFACE
    path('cart/', get_cart, name='cart'),
    path('cart/add_item/', cart_add_item, name='cart-add-item'),
    path('cart/remove_item/', cart_remove_item, name='cart-remove-item'),
    path('cart/update_item/', cart_update_item, name='cart-update-item'),
    path('cart/clear/', cart_clear, name='cart-clear'),
]
