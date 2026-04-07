from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.integrations.clients import (
    ExternalServiceError,
    OrderServiceClient,
    ServiceUnavailableError,
    UserServiceClient,
)
from apps.shipping.models import Shipment
from apps.shipping.serializers import DispatchRequestSerializer, ShipmentSerializer


class DispatchShipmentView(APIView):
    @extend_schema(
        request=DispatchRequestSerializer,
        responses={
            201: ShipmentSerializer,
            400: OpenApiResponse(description="Datos invalidos o negocio no permitido"),
            503: OpenApiResponse(description="Dependencia externa no disponible"),
        },
        examples=[
            OpenApiExample(
                "Dispatch Request",
                value={"order_id": 1001, "payment_id": 7001, "user_id": 501, "courier": "DHL"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = DispatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        order_client = OrderServiceClient()
        user_client = UserServiceClient()

        try:
            order_data = order_client.get_order(payload["order_id"])
            order_status = str(order_data.get("status", "")).upper()
            if order_status != "PAGADO":
                return Response(
                    {"detail": "El pedido debe estar en estado Pagado para generar envio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_id = payload.get("user_id") or order_data.get("user_id")
            if not user_id:
                return Response(
                    {"detail": "No se encontro user_id en la solicitud ni en el pedido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_profile = user_client.get_profile(user_id)
            delivery_address = (
                user_profile.get("shipping_address")
                or user_profile.get("address")
                or user_profile.get("direccion_envio")
            )
            if not delivery_address:
                return Response(
                    {"detail": "El usuario no tiene direccion de envio registrada."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            shipment = Shipment.objects.create(
                order_id=payload["order_id"],
                payment_id=payload["payment_id"],
                user_id=user_id,
                delivery_address=delivery_address,
                tracking_guide=Shipment.generate_tracking_guide(),
                courier=payload.get("courier") or "Paqueteria Demo",
                estimated_delivery_date=Shipment.default_estimated_date(),
            )

            order_client.patch_order_status(payload["order_id"], "ENVIADO")

        except ServiceUnavailableError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ExternalServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_201_CREATED)


class TrackShipmentView(APIView):
    @extend_schema(
        responses={
            200: ShipmentSerializer,
            404: OpenApiResponse(description="Guia de rastreo no encontrada"),
        }
    )
    def get(self, request, guide: str):
        shipment = get_object_or_404(Shipment, tracking_guide=guide)
        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_200_OK)
