from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Category, Product, Cart, CartItem
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    CartSerializer,
)


# PUBLIC_INTERFACE
@api_view(['GET'])
def health(request):
    """Simple health check endpoint.
    Returns:
        200 OK with {"message": "Server is up!"}
    """
    return Response({"message": "Server is up!"})


class DefaultPagination(PageNumberPagination):
    """Default pagination for list endpoints."""
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


# PUBLIC_INTERFACE
class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD for product categories."""
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = DefaultPagination


# PUBLIC_INTERFACE
class ProductViewSet(viewsets.ModelViewSet):
    """Product browse and admin management.
    Regular users can read; only admins can write.
    """
    queryset = Product.objects.filter(is_active=True).select_related("category").order_by('name')
    serializer_class = ProductSerializer
    pagination_class = DefaultPagination

    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


# PUBLIC_INTERFACE
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_cart(request):
    """Get current authenticated user's cart details.

    Returns:
        200 OK with serialized cart data.
        401 Unauthorized if not authenticated.
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    serializer = CartSerializer(cart, context={"request": request})
    return Response(serializer.data)


# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@transaction.atomic
def cart_add_item(request):
    """Add an item to the current user's cart.

    Expected JSON:
        {
            "product_id": <int>,
            "quantity": <int>  (optional, default 1)
        }

    Returns:
        201 Created with updated cart data.
        400 Bad Request if product invalid or quantity invalid.
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    product_id = request.data.get("product_id")
    quantity = int(request.data.get("quantity", 1))
    if not product_id or quantity < 1:
        return Response({"detail": "product_id and positive quantity are required."}, status=400)

    product = get_object_or_404(Product, pk=product_id, is_active=True)
    item, created = CartItem.objects.select_for_update().get_or_create(cart=cart, product=product)
    if created:
        item.quantity = quantity
    else:
        item.quantity += quantity
    item.save()

    return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@transaction.atomic
def cart_remove_item(request):
    """Remove a product from the cart.

    Expected JSON:
        {
            "product_id": <int>
        }
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    product_id = request.data.get("product_id")
    if not product_id:
        return Response({"detail": "product_id is required."}, status=400)
    CartItem.objects.filter(cart=cart, product_id=product_id).delete()
    return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@transaction.atomic
def cart_update_item(request):
    """Update quantity of a product in the cart.

    Expected JSON:
        {
            "product_id": <int>,
            "quantity": <int>
        }
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    product_id = request.data.get("product_id")
    quantity = request.data.get("quantity")
    if not product_id or quantity is None:
        return Response({"detail": "product_id and quantity are required."}, status=400)

    quantity = int(quantity)
    if quantity < 1:
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
    else:
        item, _ = CartItem.objects.select_for_update().get_or_create(cart=cart, product_id=product_id)
        item.quantity = quantity
        item.save()

    return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@transaction.atomic
def cart_clear(request):
    """Clear all items in the current user's cart."""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    CartItem.objects.filter(cart=cart).delete()
    return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)
