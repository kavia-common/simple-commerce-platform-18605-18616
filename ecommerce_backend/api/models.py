from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model with created_at and updated_at fields."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    """Product categories used to group products."""
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(default="", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Product(TimeStampedModel):
    """Products available for purchase."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=240, unique=True)
    description = models.TextField(default="", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    image_url = models.URLField(max_length=200, default="", blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return self.name


class Cart(TimeStampedModel):
    """One cart per user."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")

    def __str__(self) -> str:
        return f"Cart({self.user_id})"

    @property
    def items_count(self) -> int:
        return sum(i.quantity for i in self.items.all())

    @property
    def subtotal(self):
        # Sum of quantity * product.price
        from decimal import Decimal
        total = Decimal("0.00")
        for item in self.items.select_related("product"):
            total += item.quantity * item.product.price
        return total


class CartItem(TimeStampedModel):
    """Items in a cart."""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = (("cart", "product"),)

    def __str__(self) -> str:
        return f"{self.product} x {self.quantity}"

    @property
    def line_total(self):
        return self.quantity * self.product.price


class Address(TimeStampedModel):
    """User addresses for shipping and billing."""
    ADDRESS_TYPES = (
        ("shipping", "Shipping"),
        ("billing", "Billing"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default="shipping")
    full_name = models.CharField(max_length=200)
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, default="", blank=True)
    city = models.CharField(max_length=120)
    state = models.CharField(max_length=120, default="", blank=True)
    postal_code = models.CharField(max_length=30)
    country = models.CharField(max_length=2, default="US")
    phone = models.CharField(max_length=30, default="", blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "-created_at"]


class Order(TimeStampedModel):
    """Orders placed by users."""
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="shipping_orders")
    billing_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="billing_orders")
    notes = models.TextField(default="", blank=True)

    class Meta:
        ordering = ["-created_at"]


class OrderItem(TimeStampedModel):
    """Snapshot of products within an order at purchase time."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    image_url = models.URLField(max_length=200, default="", blank=True)


class Transaction(TimeStampedModel):
    """Payment transaction record."""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="transaction")
    provider = models.CharField(max_length=50, default="placeholder")
    status = models.CharField(max_length=50, default="initiated")
    reference = models.CharField(max_length=200, default="", blank=True)
    raw_payload = models.JSONField(null=True, blank=True)
