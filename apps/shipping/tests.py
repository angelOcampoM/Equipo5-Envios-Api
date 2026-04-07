from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.shipping.models import Shipment


class ShippingDispatchAPITests(APITestCase):
    def setUp(self):
        self.dispatch_url = reverse("dispatch-shipment")
        self.payload = {
            "order_id": 1001,
            "payment_id": 7001,
            "user_id": 501,
            "courier": "DHL",
        }

    @patch("apps.shipping.views.UserServiceClient.get_profile")
    @patch("apps.shipping.views.OrderServiceClient.patch_order_status")
    @patch("apps.shipping.views.OrderServiceClient.get_order")
    def test_dispatch_success(self, mock_get_order, mock_patch_status, mock_get_profile):
        mock_get_order.return_value = {"id": 1001, "status": "PAGADO", "user_id": 501}
        mock_get_profile.return_value = {
            "id": 501,
            "nombre": "Juan Perez",
            "email": "juan@example.com",
            "direccion": "Calle Falsa 123, CDMX",
        }
        mock_patch_status.return_value = {"id": 1001, "status": "ENVIADO"}

        response = self.client.post(self.dispatch_url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["order_id"], self.payload["order_id"])
        self.assertIn("tracking_id", response.data)
        self.assertEqual(Shipment.objects.count(), 1)

    @patch("apps.shipping.views.OrderServiceClient.get_order")
    def test_dispatch_rejects_unpaid_order(self, mock_get_order):
        mock_get_order.return_value = {"id": 1001, "status": "PENDIENTE", "user_id": 501}

        response = self.client.post(self.dispatch_url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Shipment.objects.count(), 0)

    @patch("apps.shipping.views.OrderServiceClient.get_order")
    def test_dispatch_rejects_user_mismatch(self, mock_get_order):
        mock_get_order.return_value = {"id": 1001, "status": "PAGADO", "user_id": 999}

        response = self.client.post(self.dispatch_url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Shipment.objects.count(), 0)

    @patch("apps.shipping.views.OrderServiceClient.get_order")
    def test_dispatch_requires_all_contract_fields(self, mock_get_order):
        incomplete_payload = {
            "order_id": 1001,
            "payment_id": 7001,
        }

        response = self.client.post(self.dispatch_url, incomplete_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("user_id", response.data)
        self.assertIn("courier", response.data)
        mock_get_order.assert_not_called()

    @patch("apps.shipping.views.UserServiceClient.get_profile")
    @patch("apps.shipping.views.OrderServiceClient.patch_order_status")
    @patch("apps.shipping.views.OrderServiceClient.get_order")
    def test_dispatch_returns_conflict_when_shipment_exists(self, mock_get_order, mock_patch_status, mock_get_profile):
        Shipment.objects.create(
            order_id=1001,
            payment_id=7001,
            user_id=501,
            delivery_address="Calle Falsa 123, CDMX",
            tracking_guide=Shipment.generate_tracking_guide(),
            courier="DHL",
            estimated_delivery_date=Shipment.default_estimated_date(),
        )

        response = self.client.post(self.dispatch_url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        mock_get_order.assert_not_called()
        mock_get_profile.assert_not_called()
        mock_patch_status.assert_not_called()


class ShippingTrackAPITests(APITestCase):
    def test_track_returns_shipment(self):
        shipment = Shipment.objects.create(
            order_id=2001,
            payment_id=8001,
            user_id=601,
            delivery_address="Avenida Reforma 100, CDMX",
            tracking_guide="TRACKING12345678",
            courier="FedEx",
            estimated_delivery_date=Shipment.default_estimated_date(),
        )

        url = reverse("track-shipment", kwargs={"tracking_id": shipment.tracking_guide})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["tracking_id"], "TRACKING12345678")

    def test_track_returns_404_when_not_found(self):
        url = reverse("track-shipment", kwargs={"tracking_id": "NOEXISTE123"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
