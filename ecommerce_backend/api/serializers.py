from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Address, Transaction

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    # PUBLIC_INTERFACE
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )

    # PUBLIC_INTERFACE
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'currency',
            'stock', 'is_active', 'image_url', 'category', 'category_id',
            'created_at', 'updated_at'
        ]


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True), source='product', write_only=True
    )
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    # PUBLIC_INTERFACE
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'line_total', 'created_at', 'updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['line_total'] = str(instance.line_total)
        return data


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    # PUBLIC_INTERFACE
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'items_count', 'subtotal', 'created_at', 'updated_at']
        read_only_fields = ['user']


class AddressSerializer(serializers.ModelSerializer):
    # PUBLIC_INTERFACE
    class Meta:
        model = Address
        fields = [
            'id', 'address_type', 'full_name', 'line1', 'line2',
            'city', 'state', 'postal_code', 'country', 'phone',
            'is_default', 'created_at', 'updated_at'
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    # PUBLIC_INTERFACE
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'unit_price', 'quantity', 'image_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['product_name', 'unit_price', 'image_url', 'product']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), source='shipping_address', write_only=True
    )
    billing_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), source='billing_address', write_only=True
    )

    # PUBLIC_INTERFACE
    class Meta:
        model = Order
        fields = [
            'id', 'status', 'total_amount', 'currency',
            'shipping_address', 'billing_address',
            'shipping_address_id', 'billing_address_id',
            'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'total_amount', 'currency', 'shipping_address', 'billing_address']


class TransactionSerializer(serializers.ModelSerializer):
    # PUBLIC_INTERFACE
    class Meta:
        model = Transaction
        fields = ['id', 'order', 'provider', 'status', 'reference', 'raw_payload', 'created_at', 'updated_at']
        read_only_fields = ['order', 'provider', 'status', 'reference', 'raw_payload']


class UserSerializer(serializers.ModelSerializer):
    # PUBLIC_INTERFACE
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    # PUBLIC_INTERFACE
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )
        # Create a cart for the new user
        Cart.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    # PUBLIC_INTERFACE
    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        attrs['user'] = user
        return attrs
