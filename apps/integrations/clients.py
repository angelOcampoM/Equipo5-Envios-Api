import os
from typing import Any

import requests


class ExternalServiceError(Exception):
    pass


class ServiceUnavailableError(ExternalServiceError):
    pass


class InvalidExternalResponseError(ExternalServiceError):
    pass


class BaseHTTPClient:
    def __init__(self, base_url_env: str, default_base_url: str):
        self.base_url = os.getenv(base_url_env, default_base_url).rstrip("/")
        self.timeout = float(os.getenv("HTTP_TIMEOUT_SECONDS", "5"))
        self.mock_enabled = os.getenv("MOCK_EXTERNAL_SERVICES", "False") == "True"
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _request_json(self, method: str, path: str, *, json_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(method=method, url=url, json=json_payload, timeout=self.timeout)
        except requests.Timeout as exc:
            raise ServiceUnavailableError("Timeout al consultar un servicio externo") from exc
        except requests.RequestException as exc:
            raise ServiceUnavailableError("No fue posible conectar con un servicio externo") from exc

        if response.status_code >= 500:
            raise ServiceUnavailableError("Servicio externo temporalmente no disponible")

        if response.status_code >= 400:
            raise ExternalServiceError(f"Error externo HTTP {response.status_code}")

        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            raise InvalidExternalResponseError("Respuesta externa no es JSON")

        try:
            data = response.json()
        except ValueError as exc:
            raise InvalidExternalResponseError("JSON externo malformado") from exc

        if not isinstance(data, dict):
            raise InvalidExternalResponseError("JSON externo invalido: se esperaba objeto")

        return data


class OrderServiceClient:
    def __init__(self):
        self.http = BaseHTTPClient("ORDER_SERVICE_BASE_URL", "http://127.0.0.1:8002")

    def get_order(self, order_id: int) -> dict[str, Any]:
        if self.http.mock_enabled:
            return {"id": order_id, "user_id": 501, "status": "PAGADO"}

        try:
            return self.http._request_json("GET", f"/api/orders/{order_id}/")
        except ExternalServiceError as exc:
            message = str(exc)
            if "HTTP 404" in message:
                raise ExternalServiceError("El pedido no existe") from exc
            raise

    def patch_order_status(self, order_id: int, status: str) -> dict[str, Any]:
        payload = {"status": status}

        if self.http.mock_enabled:
            return {"id": order_id, "status": status}

        try:
            return self.http._request_json("PATCH", f"/api/orders/{order_id}/status/", json_payload=payload)
        except ExternalServiceError as exc:
            message = str(exc)
            if "HTTP" in message:
                raise ExternalServiceError("No fue posible actualizar el estado del pedido") from exc
            raise


class UserServiceClient:
    def __init__(self):
        self.http = BaseHTTPClient("USER_SERVICE_BASE_URL", "http://127.0.0.1:8001")

    def get_profile(self, user_id: int) -> dict[str, Any]:
        if self.http.mock_enabled:
            return {
                "id": user_id,
                "nombre": "Usuario Mock",
                "email": "mock@example.com",
                "direccion": "Calle Mock 123, CDMX",
            }

        try:
            return self.http._request_json("GET", f"/api/users/{user_id}/profile/")
        except ExternalServiceError as exc:
            message = str(exc)
            if "HTTP 404" in message:
                raise ExternalServiceError("El usuario no existe") from exc
            if "HTTP" in message:
                raise ExternalServiceError("No fue posible consultar al usuario") from exc
            raise
