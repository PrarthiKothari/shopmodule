from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal, ROUND_HALF_UP
import datetime
import math
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

class Product(models.Model):
    class DeliveryType(models.TextChoices):
        STANDARD = "STANDARD", "Standard Delivery"
        EXPRESS = "EXPRESS", "Express Delivery"
        SAME_DAY = "SAME_DAY", "Same Day Delivery"
        PICKUP = "PICKUP", "Store Pickup"

    DELIVERY_TIME_MAP = {
        "STANDARD": "3-5 Business Days",
        "EXPRESS": "1-2 Business Days",
        "SAME_DAY": "Within 24 Hours",
        "PICKUP": "Immediate / Store Hours",
    }

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True, blank=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="products",
        null=True,
        blank=True,
        help_text="User who created this product"
    )

    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'), message="Base price cannot be negative.")]
    )
    gst = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(Decimal('0.00'), message="GST cannot be negative."),
            MaxValueValidator(Decimal('18.00'), message="GST cannot exceed 18%.")
        ],
        help_text="GST percentage, e.g. 18.00 for 18% (maximum 18%)"
    )
    other_taxes = models.TextField(blank=True, help_text="Other applicable tax details (e.g., Cess, surcharge)")

    delivery_type = models.CharField(max_length=20, choices=DeliveryType.choices, default=DeliveryType.STANDARD)
    delivery_time = models.CharField(max_length=100, help_text="e.g. 3-5 Business Days (auto-set by delivery type)")
    delivery_charges = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(Decimal('0.00'), message="Delivery charges cannot be negative."),
            MaxValueValidator(Decimal('100.00'), message="Delivery charges cannot exceed 100.")
        ],
        help_text="Delivery charges in Rs.  (maximum 100)"
    )

    other_information = models.TextField(blank=True, help_text="Any additional required product details")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Flag indicating if product is soft-deleted"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when product was soft-deleted"
    )

    def clean(self):
        super().clean()
        if not self.delivery_time and self.delivery_type in self.DELIVERY_TIME_MAP:
            self.delivery_time = self.DELIVERY_TIME_MAP[self.delivery_type]

        errors = {}
        if self.base_price is not None and self.base_price < 0:
            errors['base_price'] = "Base price cannot be negative."
        if self.gst is not None and self.gst < 0:
            errors['gst'] = "GST cannot be negative."
        if self.gst is not None and self.gst > 18:
            errors['gst'] = "GST cannot exceed 18%."
        if self.delivery_charges is not None and self.delivery_charges < 0:
            errors['delivery_charges'] = "Delivery charges cannot be negative."
        if self.delivery_charges is not None and self.delivery_charges > 100:
            errors['delivery_charges'] = "Delivery charges cannot exceed 100."
        if self.delivery_type == self.DeliveryType.PICKUP:
            if self.delivery_charges is not None and self.delivery_charges > Decimal('0.00'):
                errors['delivery_charges'] = "Store pickup cannot have delivery charges (must be Rs. 0.00)."
            else:
                self.delivery_charges = Decimal('0.00')
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.delivery_type == self.DeliveryType.PICKUP:
            self.delivery_charges = Decimal('0.00')
        self.full_clean()
        if not self.code:
            super().save(*args, **kwargs)
            self.code = f"PRD-{self.id:06d}"
            kwargs.pop('force_insert', None)
        super().save(*args, **kwargs)

    @property
    def primary_image(self):
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()

    @property
    def gst_amount(self):
        if self.base_price and self.gst:
            return (self.base_price * self.gst) / Decimal("100").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return Decimal("0.00")

    @property
    def total_price(self):
        price = self.base_price or Decimal("0.00")
        gst_amt = self.gst_amount
        charges = self.delivery_charges or Decimal("0.00")
        return price + gst_amt + charges

    @property
    def purge_date(self):
        if self.deleted_at:
            return self.deleted_at + datetime.timedelta(days=30)
        return None

    @property
    def days_until_purge(self):
        if self.deleted_at:
            target = self.deleted_at + datetime.timedelta(days=30)
            remaining_seconds = (target - timezone.now()).total_seconds()
            if remaining_seconds <= 0:
                return 0
            return int(math.ceil(remaining_seconds / 86400))
        return None

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def revive(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.product.name} Image"

class ProductURL(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="urls")
    title = models.CharField(max_length=100, blank=True)
    url = models.URLField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title or self.url
    