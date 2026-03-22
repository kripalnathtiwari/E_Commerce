from django.db import models
from category.models import Category
from django.conf import settings
import uuid


class Product(models.Model):

    distributor = models.ForeignKey(
        "orders.Distributor",   # ✅ correct app
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="products"
    )

    product_name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    price = models.IntegerField()
    image = models.ImageField(upload_to='photos/products')
    stock = models.IntegerField()
    is_available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name

    @property
    def colors(self):
        return self.variation_set.filter(variation_category__iexact='color', is_active=True)

    @property
    def sizes(self):
        return self.variation_set.filter(variation_category__iexact='size', is_active=True)

    def get_image_for_color(self, color):
        """Get the image for a specific color, or the main image if no color-specific image exists"""
        if color:
            product_image = self.product_images.filter(variation__variation_value__iexact=color).first()
            if product_image:
                return product_image.image.url
        return self.image.url

    def averageReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(average=models.Avg('rating'))
        avg = 0
        if reviews['average'] is not None:
            avg = float(reviews['average'])
        return avg

    def countReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(count=models.Count('id'))
        count = 0
        if reviews['count'] is not None:
            count = int(reviews['count'])
        return count

class VariationManager(models.Manager):
    def colors(self):
        return super(VariationManager, self).filter(variation_category='color', is_active=True)

    def sizes(self):
        return super(VariationManager, self).filter(variation_category='size', is_active=True)

variation_category_choice = (
    ('color', 'color'),
    ('size', 'size'),
)

class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation_category = models.CharField(max_length=100, choices=variation_category_choice)
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now=True)

    objects = VariationManager()

    def __str__(self):
        return self.variation_value


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_images')
    variation = models.ForeignKey(Variation, on_delete=models.CASCADE, null=True, blank=True)  # For color variations
    image = models.ImageField(upload_to='photos/products')
    is_main = models.BooleanField(default=False)  # To mark the main image

    def __str__(self):
        return f"{self.product.product_name} - {self.variation.variation_value if self.variation else 'Main'}"


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    quantity = models.IntegerField(default=1)

    def sub_total(self):
        if self.product.stock <= 0:
            return 0
        return self.product.price * self.quantity


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="store_order_items")
    distributor = models.ForeignKey(
        "orders.Distributor",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    STATUS = (
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )
    item_id = models.CharField(max_length=20, unique=True, editable=False, null=True)
    quantity = models.IntegerField()
    price = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS, default='Pending')
    updated_at = models.DateTimeField(auto_now=True)
    variations = models.ManyToManyField(Variation, blank=True, related_name="store_variations")

    def save(self, *args, **kwargs):
        if not self.item_id:
            self.item_id = 'ITM-' + str(uuid.uuid4()).upper()[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Item {self.item_id} - {self.product.product_name}"


class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    image = models.ImageField(upload_to='reviews/', null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject