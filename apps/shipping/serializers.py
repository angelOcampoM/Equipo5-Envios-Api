from rest_framework import serializers

from apps.shipping.models import Shipment


class DispatchRequestSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    payment_id = serializers.IntegerField(min_value=1)
    user_id = serializers.IntegerField(min_value=1, required=False)
    courier = serializers.CharField(max_length=100, required=False, allow_blank=True)


class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = [
            "id",
            "order_id",
            "payment_id",
            "user_id",
            "delivery_address",
            "tracking_guide",
            "courier",
            "estimated_delivery_date",
            "status",
            "created_at",
            "updated_at",
        ]
