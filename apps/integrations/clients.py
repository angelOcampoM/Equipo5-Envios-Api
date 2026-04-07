import os
from typing import Any

import requests


class ExternalServiceError(Exception):
    pass


class ServiceUnavailableError(ExternalServiceError):
    pass


class OrderServiceClient:
    def __init__(self):
        self.base_url = os.getenv("ORDER_SERVICE_BASE_URL", "http://127.0.0.1:8002").rstrip("/")
        self.timeout = int(os.getenv("HTTP_TIMEOUT_SECONDS", "5"))

    def get_order(self, order_id: int) -> dict[str, Any]:
        url = f"{self.base_url}/api/orders/{order_id}/"
        try:
            response = requests.get(url, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ServiceUnavailableError("El servicio de pedidos no responde") from exc

        if response.status_code == 404:
            raise ExternalServiceError("El pedido no existe")
        if response.status_code >= 500:
            raise ServiceUnavailableError("El servicio de pedidos no esta disponible")
        if response.status_code >= 400:
            raise ExternalServiceError("No fue posible consultar el pedido")

        return response.json()

    def patch_order_status(self, order_id: int, status: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/orders/{order_id}/status/"
        payload = {"status": status}
        try:
            response = requests.patch(url, json=payload, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ServiceUnavailableError("No fue posible actualizar el estado del pedido") from exc

        if response.status_code >= 500:
            raise ServiceUnavailableError("El servicio de pedidos no esta disponible")
        if response.status_code >= 400:
            raise ExternalServiceError("No fue posible actualizar el estado del pedido")

        return response.json()


class UserServiceClient:
    def __init__(self):
        self.base_url = os.getenv("USER_SERVICE_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
        self.timeout = int(os.getenv("HTTP_TIMEOUT_SECONDS", "5"))

    def get_profile(self, user_id: int) -> dict[str, Any]:
        url = f"{self.base_url}/api/users/{user_id}/profile/"
        try:
            response = requests.get(url, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ServiceUnavailableError("El servicio de usuarios no responde") from exc

        if response.status_code == 404:
            raise ExternalServiceError("El usuario no existe")
        if response.status_code >= 500:
            raise ServiceUnavailableError("El servicio de usuarios no esta disponible")
        if response.status_code >= 400:
            raise ExternalServiceError("No fue posible consultar al usuario")

        return response.json()
