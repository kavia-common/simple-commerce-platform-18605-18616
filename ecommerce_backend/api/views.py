from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Address
from .serializers import (
    CategorySerializer, ProductSerializer, CartSerializer, CartItemSerializer,
    OrderSerializer, AddressSerializer, RegisterSerializer, LoginSerializer, UserSerializer
)

User = get_user_model()


class DefaultPagination(PageNumberPagination):
    """
    Default pagination for list endpoints.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# PUBLIC_INTERFACE
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health(request):
    """
    Health check endpoint.

    Returns:
      200 OK with a simple informative message.
    """
    return Response({"message": "Server is up!"})


class CategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD for product categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = DefaultPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug', 'description']
    ordering_fields = ['name', 'created_at']


class ProductViewSet(viewsets.ModelViewSet):
    """
    Product browse and admin management.
    Regular users can read; only admins can write.
    """
    queryset = Product.objects.all().select_related('category')
    serializer_class = ProductSerializer
    pagination_class = DefaultPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'slug', 'description', 'category__name']
    ordering_fields = ['name', 'price', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        qs = super().get_queryset()
        # Only return active products to non-admins
        if not self.request.user.is_staff:
            qs = qs.filter(is_active=True)
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(Q(category__slug=category) | Q(category__id=category))
        return qs


class AddressViewSet(viewsets.ModelViewSet):
    """
    Manage user addresses. Users can only access their own addresses.
    """
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'line1', 'city', 'postal_code', 'country']
    ordering_fields = ['created_at']

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).order_by('-is_default', '-created_at')

    def perform_create(self, serializer):
        # If is_default set, unset others of same type for user
        addr = serializer.save(user=self.request.user)
        if addr.is_default:
            Address.objects.filter(user=self.request.user, address_type=addr.address_type).exclude(id=addr.id).update(is_default=False)


class CartViewSet(viewsets.ViewSet):
    """
    Retrieve and modify the current user's cart.
    """
    permission_classes = [permissions.IsAuthenticated]

    # PUBLIC_INTERFACE
    def list(self, request):
        """
        summary: Get current user's cart
        description: Retrieve the cart for the authenticated user.
        responses:
          200: Cart object with items and totals.
        """
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return Response(CartSerializer(cart).data)

    # PUBLIC_INTERFACE
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """
        summary: Add item to cart
        description: Add a product with quantity to the user's cart.
        """
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data['product']
        quantity = serializer.validated_data.get('quantity', 1)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity})
        if not created:
            item.quantity += quantity
            item.save()
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)

    # PUBLIC_INTERFACE
    @action(detail=False, methods=['post'])
    def update_item(self, request):
        """
        summary: Update quantity of an item in the cart
        """
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data['product']
        quantity = serializer.validated_data.get('quantity', 1)
        try:
            item = CartItem.objects.get(cart=cart, product=product)
        except CartItem.DoesNotExist:
            return Response({'detail': 'Item not found in cart.'}, status=status.HTTP_404_NOT_FOUND)
        if quantity <= 0:
            item.delete()
        else:
            item.quantity = quantity
            item.save()
        return Response(CartSerializer(cart).data)

    # PUBLIC_INTERFACE
    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """
        summary: Remove item from cart
        """
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'detail': 'product_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        return Response(CartSerializer(cart).data)

    # PUBLIC_INTERFACE
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """
        summary: Clear cart
        """
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response(CartSerializer(cart).data)


class OrderViewSet(viewsets.ViewSet):
    """
    Order creation from cart and list/retrieve of user's orders.
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination

    # PUBLIC_INTERFACE
    def list(self, request):
        """
        summary: List current user's orders
        """
        qs = Order.objects.filter(user=request.user).order_by('-created_at')
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = OrderSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    # PUBLIC_INTERFACE
    def retrieve(self, request, pk=None):
        """
        summary: Retrieve an order by id for current user
        """
        try:
            order = Order.objects.get(pk=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order).data)

    # PUBLIC_INTERFACE
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """
        summary: Create an order from the current user's cart
        description: Uses provided shipping_address_id and billing_address_id. Creates Order and OrderItems, reduces stock, and clears the cart.
        """
        cart, _ = Cart.objects.get_or_create(user=request.user)
        if cart.items.count() == 0:
            return Response({'detail': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        shipping_address_id = request.data.get('shipping_address_id')
        billing_address_id = request.data.get('billing_address_id')
        if not shipping_address_id or not billing_address_id:
            return Response({'detail': 'shipping_address_id and billing_address_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            shipping_address = Address.objects.get(id=shipping_address_id, user=request.user)
            billing_address = Address.objects.get(id=billing_address_id, user=request.user)
        except Address.DoesNotExist:
            return Response({'detail': 'Invalid address id(s).'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # calculate total and check stock
            total = 0
            for item in cart.items.select_related('product'):
                if item.product.stock < item.quantity:
                    return Response({'detail': f'Insufficient stock for {item.product.name}.'}, status=status.HTTP_400_BAD_REQUEST)
                total += item.product.price * item.quantity

            order = Order.objects.create(
                user=request.user,
                status='pending',
                total_amount=total,
                currency='USD',
                shipping_address=shipping_address,
                billing_address=billing_address,
            )
            # Create order items and decrement stock
            bulk_items = []
            for item in cart.items.select_related('product'):
                product = item.product
                product.stock -= item.quantity
                product.save(update_fields=['stock'])
                bulk_items.append(OrderItem(
                    order=order,
                    product=product,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=item.quantity,
                    image_url=product.image_url,
                ))
            OrderItem.objects.bulk_create(bulk_items)
            cart.items.all().delete()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


# Auth views
class RegisterView(generics.CreateAPIView):
    """
    Register a new user and create a cart.
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(generics.GenericAPIView):
    """
    Login endpoint returning a simple session-based response.
    In production, integrate token or JWT auth as needed.
    """
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    # PUBLIC_INTERFACE
    def post(self, request):
        """
        summary: Log a user in (session-based)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        from django.contrib.auth import login
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    """
    Logout the current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    # PUBLIC_INTERFACE
    def post(self, request):
        """
        summary: Log current user out
        """
        from django.contrib.auth import logout
        logout(request)
        return Response({'detail': 'Logged out.'}, status=status.HTTP_200_OK)


class MeView(generics.RetrieveAPIView):
    """
    Get details of current authenticated user.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    # PUBLIC_INTERFACE
    def get_object(self):
        """
        summary: Get current user profile
        """
        return self.request.user
