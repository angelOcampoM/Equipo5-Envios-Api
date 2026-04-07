# Equipo 5 - API de Envios y Logistica (Shipping Service)

Microservicio del sistema de e-commerce distribuido encargado de gestionar el envio de pedidos pagados.

## 1) Objetivo del microservicio

Responsabilidad del Equipo 5:
- Recibir un pedido pagado.
- Generar la guia de rastreo y datos logisticos.
- Exponer consulta de rastreo.
- Notificar a Pedidos (Equipo 3) para cambiar estado a `ENVIADO`.
- Consumir Usuarios (Equipo 1) para obtener direccion de entrega.

## 2) Endpoints del Equipo 5

### POST /api/shipping/dispatch/
Genera el envio para un pedido pagado.

Request JSON (base acordada):
```json
{
  "order_id": 1001,
  "payment_id": 7001,
  "user_id": 501,
  "courier": "DHL"
}
```

Response 201 JSON (ejemplo):
```json
{
  "id": 1,
  "order_id": 1001,
  "payment_id": 7001,
  "user_id": 501,
  "delivery_address": "Calle 123, CDMX",
  "tracking_guide": "5A1C0E88D3774A15",
  "courier": "DHL",
  "estimated_delivery_date": "2026-04-12",
  "status": "PREPARING",
  "created_at": "2026-04-06T18:00:00Z",
  "updated_at": "2026-04-06T18:00:00Z"
}
```

Errores esperados:
- 400: pedido no pagado, usuario invalido o sin direccion.
- 503: servicio de Pedidos o Usuarios no disponible.

### GET /api/shipping/track/<guia>/
Consulta estado del envio.

Response 200 JSON:
```json
{
  "id": 1,
  "order_id": 1001,
  "payment_id": 7001,
  "user_id": 501,
  "delivery_address": "Calle 123, CDMX",
  "tracking_guide": "5A1C0E88D3774A15",
  "courier": "DHL",
  "estimated_delivery_date": "2026-04-12",
  "status": "PREPARING",
  "created_at": "2026-04-06T18:00:00Z",
  "updated_at": "2026-04-06T18:00:00Z"
}
```

## 3) Arquitectura base incluida en este repositorio

```text
Equipo5-Envios-Api/
  manage.py
  requirements.txt
  .env.example
  shipping_service/
    settings.py
    urls.py
    asgi.py
    wsgi.py
  apps/
    integrations/
      clients.py
    shipping/
      migrations/
        0001_initial.py
      admin.py
      apps.py
      models.py
      serializers.py
      urls.py
      views.py
      tests.py
```

## 4) Modelo de datos inicial

Entidad `Shipment`:
- `order_id` (id del pedido)
- `payment_id` (id del pago)
- `user_id` (id del cliente)
- `delivery_address` (direccion fisica)
- `tracking_guide` (guia unica)
- `courier` (paqueteria)
- `estimated_delivery_date` (fecha estimada)
- `status` (`PREPARING`, `IN_TRANSIT`, `DELIVERED`)
- `created_at`, `updated_at`

## 5) Contrato de integracion con otros equipos (propuesta base)

### Equipo 5 -> Equipo 3 (Pedidos)
1. Validar pedido pagado:
- GET `/api/orders/<id>/`
- Campo esperado en respuesta: `status` (debe ser `PAGADO`) y `user_id`.

2. Actualizar pedido enviado:
- PATCH `/api/orders/<id>/status/`
```json
{
  "status": "ENVIADO"
}
```

### Equipo 5 -> Equipo 1 (Usuarios)
1. Obtener direccion de envio:
- GET `/api/users/<id>/profile/`
- Campo esperado: `shipping_address` (o `address`/`direccion_envio` de forma temporal mientras se alinea contrato).

## 6) Reparto del trabajo para 4 integrantes

### Angel (tu) - Lider tecnico e integracion final
Rama: `feature/angel-integration-release`
- Coordinar contratos JSON finales con Equipos 1 y 3.
- Integrar y resolver conflictos de PRs.
- Definir version candidata y checklist de release.
- Entregable: rama estable lista para merge a `main`.

### Antonio - Dominio y modelo de envios
Rama: `feature/antonio-shipping-models`
- Refinar modelo `Shipment` y reglas de negocio.
- Agregar indices, restricciones y validaciones.
- Mejorar admin y preparar datos semilla.
- Entregable: modelo estable y migraciones limpias.

### Amador - API y documentacion
Rama: `feature/amador-api-docs`
- Fortalecer `dispatch` y `track` (serializers, validaciones, errores).
- Documentar en Swagger (`/api/docs/`) con ejemplos reales.
- Definir catalogo de errores JSON estandar.
- Entregable: API consistente y documentada.

### Aidee - Calidad y pruebas
Rama: `feature/aidee-testing-postman`
- Pruebas unitarias e integracion de endpoints.
- Coleccion Postman del Equipo 5.
- Script local de validacion (test + lint basico).
- Entregable: evidencia de calidad y criterios de aceptacion.

## 7) Flujo de ramas recomendado

1. `master` (base estable inicial).
2. Crear 4 ramas feature (una por integrante).
3. Cada integrante abre Pull Request contra `develop` (si crean `develop`) o `master`.
4. Revisiones cruzadas minimas: 1 aprobacion por PR.
5. Merge sin romper tests ni contratos JSON.

Ramas oficiales del equipo:
- `feature/angel-integration-release`
- `feature/antonio-shipping-models`
- `feature/amador-api-docs`
- `feature/aidee-testing-postman`

## 8) Arranque rapido local (sin entorno virtual)

1. Instalar dependencias en Python del sistema:
```bash
python3 -m pip install --user -r requirements.txt
```

2. Configurar variables de entorno:
```bash
cp .env.example .env
```

3. Ejecutar migraciones:
```bash
python3 manage.py migrate
```

4. Levantar servidor:
```bash
python3 manage.py runserver 8005
```

5. Documentacion Swagger:
- `http://127.0.0.1:8005/api/docs/`

## 9) Checklist de Fase 1 (antes de codificar mas)

- Acordar JSON final con Equipo 1 y Equipo 3 (nombres de campos exactos).
- Acordar codigos de estado y errores compartidos.
- Definir puertos/IP en red local para pruebas de integracion.
- Definir criterio de "pedido pagado" y transicion a "enviado".

## 10) Notas de coordinacion para su integracion final

- Si Pedidos o Usuarios no responde, regresar `503` con mensaje claro.
- No exponer datos sensibles en logs o respuestas.
- Mantener compatibilidad JSON para evitar bloqueos entre equipos.
- Primero estabilizar contrato, luego optimizar implementacion.
