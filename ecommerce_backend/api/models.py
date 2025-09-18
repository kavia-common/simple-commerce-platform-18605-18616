from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TimeStampedModel(models.Model):
    """
    Abstract base model with created/updated timestamps.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    """
    Product category for organizing products.
    """
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Product(TimeStampedModel):
    """
    A product listing with stock tracking and pricing.
    """
    category = models.ForeignKey(Category, related_name='products', on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=240, unique=True)
    description = models.TextField(blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    image_url = models.URLField(blank=True, default='')

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.currency} {self.price})"


class Cart(TimeStampedModel):
    """
    Shopping cart owned by a user.
    """
    user = models.OneToOneField(User, related_name='cart', on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"Cart<{self.user_id}>"

    @property
    def items_count(self) -> int:
        return sum([ci.quantity for ci in self.items.all()])

    @property
    def subtotal(self):
        from decimal import Decimal
        total = Decimal('0.00')
        for item in self.items.select_related('product'):
            total += item.product.price * item.quantity
        return total


class CartItem(TimeStampedModel):
    """
    Line item in a cart.
    """
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='cart_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self) -> str:
        return f"{self.quantity} x {self.product.name}"

    @property
    def line_total(self):
        return self.product.price * self.quantity


class Address(TimeStampedModel):
    """
    Saved user address for shipping/billing.
    """
    ADDRESS_TYPES = (
        ('shipping', 'Shipping'),
        ('billing', 'Billing'),
    )
    user = models.ForeignKey(User, related_name='addresses', on_delete=models.CASCADE)
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default='shipping')
    full_name = models.CharField(max_length=200)
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, blank=True, default='')
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120, blank=True, default='')
    postal_code = models.CharField(max_length=30)
    country = models.CharField(max_length=2, default='US')
    phone = models.CharField(max_length=30, blank=True, default='')
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self) -> str:
        return f"{self.full_name} - {self.line1}, {self.city}"


class Order(TimeStampedModel):
    """
    An order placed by a user.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(User, related_name='orders', on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    shipping_address = models.ForeignKey(Address, related_name='shipping_orders', on_delete=models.PROTECT)
    billing_address = models.ForeignKey(Address, related_name='billing_orders', on_delete=models.PROTECT)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Order#{self.id} {self.user_id} - {self.status}"


class OrderItem(TimeStampedModel):
    """
    Item within an order with snapshot of price.
    """
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.PROTECT)
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    image_url = models.URLField(blank=True, default='')

    def __str__(self) -> str:
        return f"{self.quantity} x {self.product_name}"


class Transaction(TimeStampedModel):
    """
    Placeholder for payment transaction records.
    For future Supabase or external payment provider integration.
    """
    order = models.OneToOneField(Order, related_name='transaction', on_delete=models.CASCADE)
    provider = models.CharField(max_length=50, default='placeholder')
    status = models.CharField(max_length=50, default='initiated')
    reference = models.CharField(max_length=200, blank=True, default='')
    raw_payload = models.JSONField(blank=True, null=True)

    def __str__(self) -> str:
        return f"Txn<{self.provider}:{self.status}>#{self.id}"
