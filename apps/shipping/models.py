import uuid
from datetime import timedelta

from django.core.exceptions import ValidationError
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
        constraints = [
            models.CheckConstraint(check=models.Q(order_id__gt=0), name="shipping_order_id_gt_0"),
            models.CheckConstraint(check=models.Q(payment_id__gt=0), name="shipping_payment_id_gt_0"),
            models.CheckConstraint(check=models.Q(user_id__gt=0), name="shipping_user_id_gt_0"),
            models.UniqueConstraint(fields=["order_id"], name="unique_shipment_per_order")
        ]

    def clean(self):
        super().clean()
        if not self.delivery_address or len(self.delivery_address.strip()) == 0:
            raise ValidationError({"delivery_address": "La direccion de entrega no puede estar vacia."})
        
        # Validar que si es un nuevo registro, la entrega no sea en el pasado.
        if self._state.adding and self.estimated_delivery_date and self.estimated_delivery_date < timezone.now().date():
            raise ValidationError({"estimated_delivery_date": "La fecha estimada de entrega no puede ser en el pasado."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Shipment(order={self.order_id}, guide={self.tracking_guide})"

    @staticmethod
    def generate_tracking_guide() -> str:
        return uuid.uuid4().hex[:16].upper()

    @staticmethod
    def default_estimated_date(days: int = 5):
        return timezone.now().date() + timedelta(days=days)
