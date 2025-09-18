from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    health, CategoryViewSet, ProductViewSet, CartViewSet, OrderViewSet,
    AddressViewSet, RegisterView, LoginView, LogoutView, MeView
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'addresses', AddressViewSet, basename='address')

urlpatterns = [
    path('health/', health, name='Health'),
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
]
