from django.db import models
from django.contrib.auth import get_user_model
from store.models import Product, Variation  # Added Variation
from django.conf import settings
import uuid
from E_Commerce.custom_storages import S3DesignStorage
User = get_user_model()


# ================= ADDRESS =================
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)
    house = models.CharField(max_length=255)
    area = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.city}"


# ================= DESIGN =================
class UploadedDesign(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="uploaded_designs")
    image = models.ImageField(upload_to="designs/", storage=S3DesignStorage())
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Design by {self.user}"


# ================= DISTRIBUTOR =================
class Distributor(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="distributor_profile"
    )
    phone = models.CharField(max_length=15)
    city = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username


# ================= PRINT ORDER =================
class PrintOrder(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="print_orders"
    )

    product = models.ForeignKey(
    Product,
    on_delete=models.CASCADE,
    related_name="order_order_items"
)

    design = models.ForeignKey(
        UploadedDesign,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    address = models.ForeignKey(Address, on_delete=models.CASCADE)

    distributor = models.ForeignKey(
        Distributor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # VARIATIONS
    variations = models.ManyToManyField(Variation, blank=True)

    # Link to Store OrderItem
    store_order_item = models.ForeignKey(
        'store.OrderItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="print_orders"
    )

    # PAYMENT
    PAYMENT_METHODS = [
        ("card", "Card/UPI"),
        ("qr", "QR Payment"),
        ("cod", "Cash on Delivery"),
    ]

    PAYMENT_STATUS = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("cod_confirmed", "COD Confirmed"),
        ("verification_pending", "QR Verification Pending"),
    ]

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS, default="pending")

    # DELIVERY
    DELIVERY_STATUS = [
        ("pending", "Pending"),
        ("assigned", "Assigned"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
    ]

    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS,
        default="pending"
    )

    quantity = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=8, decimal_places=2)

    payment_proof = models.ImageField(upload_to="payment_proofs/", storage=S3DesignStorage(), blank=True, null=True)

    # Simulated Card Details
    card_number = models.CharField(max_length=20, blank=True, null=True)
    expiry_date = models.CharField(max_length=10, blank=True, null=True)
    cvv = models.CharField(max_length=4, blank=True, null=True)

    item_id = models.CharField(max_length=20, unique=True, editable=False, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.item_id:
            self.item_id = 'PRN-' + str(uuid.uuid4()).replace('-', '').upper()[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Print Order {self.item_id} - {self.user}"



class Order(models.Model):

    STATUS = (
        ('pending','Pending'),
        ('confirmed','Confirmed'),
        ('shipped','Shipped'),
        ('out_for_delivery','Out for Delivery'),
        ('delivered','Delivered'),
    )

    PAYMENT_STATUS = (
        ('pending','Pending'),
        ('paid','Paid'),
        ('failed','Failed'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    distributor = models.ForeignKey(
        Distributor,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    address = models.TextField()

    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='pending'
    )

    delivery_status = models.CharField(
        max_length=30,
        choices=STATUS,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id}"
    
class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="orders_order_items"
    )

    quantity = models.IntegerField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    variations = models.ManyToManyField(
        Variation,
        blank=True,
        related_name="orders_variations"
    )

    item_id = models.CharField(max_length=20, unique=True, editable=False, null=True)

    def save(self, *args, **kwargs):
        if not self.item_id:
            self.item_id = 'ITM-' + str(uuid.uuid4()).replace('-', '').upper()[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Item {self.item_id} - {self.product.product_name}"


# ================= RETURN =================
class Return(models.Model):
    RETURN_STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("completed", "Completed"),
    ]

    order = models.ForeignKey(
        'store.Order',
        on_delete=models.CASCADE,
        related_name="returns"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="returns"
    )

    issue_description = models.TextField(
        help_text="Describe the issue with the product"
    )

    photo = models.ImageField(
        upload_to="return_photos/",
        storage=S3DesignStorage(),
        help_text="Upload photo of the defective product"
    )

    return_status = models.CharField(
        max_length=20,
        choices=RETURN_STATUS,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Return for Order {self.order.id}"

    def is_within_return_window(self):
        """Check if return is within 7 days of order delivery"""
        from datetime import timedelta
        from django.utils import timezone
        
        if self.order.delivery_status != 'delivered':
            return False
        
        # Get the delivered date from PrintOrder if available
        print_orders = PrintOrder.objects.filter(
            store_order_item__id__in=self.order.items.values('id')
        )
        
        if print_orders.exists():
            delivered_date = print_orders.first().created_at
            days_passed = (timezone.now() - delivered_date).days
            return days_passed <= 7
        
        return False