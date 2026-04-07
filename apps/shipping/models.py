import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone


class ShippingStatus(models.TextChoices):
    PREPARING = "PREPARING", "Preparando"
    IN_TRANSIT = "IN_TRANSIT", "En transito"
    DELIVERED = "DELIVERED", "Entregado"


class Shipment(models.Model):
    order_id = models.PositiveBigIntegerField(db_index=True)
    payment_id = models.PositiveBigIntegerField(db_index=True)
    user_id = models.PositiveBigIntegerField(db_index=True)
    delivery_address = models.TextField()
    tracking_guide = models.CharField(max_length=32, unique=True, db_index=True)
    courier = models.CharField(max_length=100, default="Paqueteria Demo")
    estimated_delivery_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=ShippingStatus.choices,
        default=ShippingStatus.PREPARING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Shipment(order={self.order_id}, guide={self.tracking_guide})"

    @staticmethod
    def generate_tracking_guide() -> str:
        return uuid.uuid4().hex[:16].upper()

    @staticmethod
    def default_estimated_date(days: int = 5):
        return timezone.now().date() + timedelta(days=days)
