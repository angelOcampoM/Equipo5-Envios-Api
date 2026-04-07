from django.urls import path

from apps.shipping.views import DispatchShipmentView, TrackShipmentView

urlpatterns = [
    path("dispatch/", DispatchShipmentView.as_view(), name="dispatch-shipment"),
    path("track/<str:guide>/", TrackShipmentView.as_view(), name="track-shipment"),
]
