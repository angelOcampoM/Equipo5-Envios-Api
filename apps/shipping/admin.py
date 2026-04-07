from django.contrib import admin

from apps.shipping.models import Shipment


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_id",
        "payment_id",
        "user_id",
        "tracking_guide",
        "courier",
        "status",
        "estimated_delivery_date",
        "created_at",
    )
    search_fields = ("tracking_guide", "order_id", "payment_id", "user_id")
    list_filter = ("status", "courier", "created_at")
    date_hierarchy = "created_at"
    readonly_fields = ("tracking_guide", "created_at", "updated_at")
