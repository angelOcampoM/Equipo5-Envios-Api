from rest_framework import serializers

from apps.shipping.models import Shipment


class DispatchRequestSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)
    payment_id = serializers.IntegerField(min_value=1)
    user_id = serializers.IntegerField(min_value=1)
    courier = serializers.CharField(max_length=100)


class ShipmentSerializer(serializers.ModelSerializer):
    tracking_id = serializers.CharField(source="tracking_guide", read_only=True)

    class Meta:
        model = Shipment
        fields = [
            "id",
            "order_id",
            "payment_id",
            "user_id",
            "delivery_address",
            "tracking_guide",
            "tracking_id",
            "courier",
            "estimated_delivery_date",
            "status",
            "created_at",
            "updated_at",
        ]
