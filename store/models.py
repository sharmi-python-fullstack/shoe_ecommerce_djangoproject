from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Product(models.Model):
    """A shoe product displayed in the catalogue."""
    CATEGORY_CHOICES = [
        ('women', 'Womens'),
        ('men', 'Mens'),
        ('kids', 'Kids'),
        ('general', 'General'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='general')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-subscribed_at']

    def __str__(self):
        return self.email


class ContactInquiry(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.created_at:%Y-%m-%d}'


class Cart(models.Model):
    """One cart per authenticated user (or session‑based for anon)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=8, blank=True)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity}× {self.product.name}"

    @property
    def total_price(self):
        return self.product.price * self.quantity

class Order(models.Model):
    """An order created when a customer starts checkout."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    shipping_address = models.CharField(max_length=255)
    billing_address = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    checkout_session_key = models.CharField(max_length=40, blank=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField()
    size = models.CharField(max_length=8, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)  # snapshot of product price

    def __str__(self):
        return f"{self.quantity}× {self.product.name if self.product else 'Deleted'}"

    @property
    def total_price(self):
        return self.price * self.quantity
