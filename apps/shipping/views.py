from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.integrations.clients import (
    ExternalServiceError,
    InvalidExternalResponseError,
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
            409: OpenApiResponse(description="El pedido ya tiene envio"),
            502: OpenApiResponse(description="Respuesta invalida de una dependencia externa"),
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

        if Shipment.objects.filter(order_id=payload["order_id"]).exists():
            return Response(
                {"detail": "Ya existe un envio para este order_id."},
                status=status.HTTP_409_CONFLICT,
            )

        order_client = OrderServiceClient()
        user_client = UserServiceClient()
        shipment = None

        try:
            order_data = order_client.get_order(payload["order_id"])

            external_order_id = order_data.get("id")
            try:
                external_order_id_int = int(external_order_id)
            except (TypeError, ValueError):
                return Response(
                    {"detail": "La respuesta de pedidos no incluye un id valido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if external_order_id_int != payload["order_id"]:
                return Response(
                    {"detail": "La respuesta de pedidos no coincide con el order_id solicitado."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            order_status = str(order_data.get("status", "")).upper()
            if order_status != "PAGADO":
                return Response(
                    {"detail": "El pedido debe estar en estado Pagado para generar envio."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            order_user_id = order_data.get("user_id")
            try:
                order_user_id_int = int(order_user_id)
            except (TypeError, ValueError):
                return Response(
                    {"detail": "El pedido no contiene user_id valido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if order_user_id_int != payload["user_id"]:
                return Response(
                    {"detail": "El user_id de la solicitud no coincide con el del pedido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_id = payload["user_id"]

            user_profile = user_client.get_profile(user_id)
            delivery_address = (
                user_profile.get("shipping_address")
                or user_profile.get("address")
                or user_profile.get("direccion_envio")
                or user_profile.get("direccion")
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
                courier=payload["courier"],
                estimated_delivery_date=Shipment.default_estimated_date(),
            )

            order_client.patch_order_status(payload["order_id"], "ENVIADO")

        except IntegrityError:
            return Response(
                {"detail": "Ya existe un envio para este pedido."},
                status=status.HTTP_409_CONFLICT,
            )
        except InvalidExternalResponseError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except ServiceUnavailableError as exc:
            if shipment and shipment.pk:
                shipment.delete()
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except ExternalServiceError as exc:
            if shipment and shipment.pk:
                shipment.delete()
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_201_CREATED)


class TrackShipmentView(APIView):
    @extend_schema(
        responses={
            200: ShipmentSerializer,
            404: OpenApiResponse(description="Guia de rastreo no encontrada"),
        }
    )
    def get(self, request, tracking_id: str):
        shipment = get_object_or_404(Shipment, tracking_guide=tracking_id)
        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_200_OK)
