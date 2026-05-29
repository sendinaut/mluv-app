import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models


class Status(models.TextChoices):
    NEW = "NEW"
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"


class FiscalStatus(models.TextChoices):
    PENDING = "PENDING"
    DONE = "DONE"
    FAILED = "FAILED"


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(
        get_user_model(), on_delete=models.PROTECT, related_name="orders"
    )

    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)

    lessons_quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )

    price_per_lesson = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    fiscal_status = models.CharField(
        max_length=20, choices=FiscalStatus.choices, default=FiscalStatus.PENDING
    )
    fiscal_receipt_id = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.customer_email = self.user.email
        self.customer_name = self.user.full_name or self.user.get_full_name()
        self.customer_phone = self.user.phone_number or ""

        self.total_amount = self.price_per_lesson * self.lessons_quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_name} - {self.lessons_quantity} lessons"


class Payment(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="transactions"
    )
    external_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)
    raw_response = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
