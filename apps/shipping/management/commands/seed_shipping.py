from django.core.management.base import BaseCommand
from apps.shipping.models import Shipment, ShippingStatus
import random

class Command(BaseCommand):
    help = 'Prepara datos semilla para la tabla Shipment'

    def handle(self, *args, **options):
        initial_count = Shipment.objects.count()
        if initial_count > 0:
            self.stdout.write(self.style.WARNING(f"La base de datos ya contiene {initial_count} envios. Se omitio la creacion de datos semilla para duplicar."))
            return

        shipments = []
        for i in range(1, 11):
            shipment = Shipment(
                order_id=1000 + i,
                payment_id=7000 + i,
                user_id=500 + (i % 3) + 1,  # Users 501, 502, 503
                delivery_address=f"Av. Principal {i}, Col. Centro, CDMX",
                tracking_guide=Shipment.generate_tracking_guide(),
                courier=random.choice(["DHL", "FedEx", "Estafeta"]),
                estimated_delivery_date=Shipment.default_estimated_date(random.randint(3, 10)),
                status=random.choice([status[0] for status in ShippingStatus.choices])
            )
            shipment.clean()
            shipments.append(shipment)
        
        Shipment.objects.bulk_create(shipments)
        
        self.stdout.write(self.style.SUCCESS(f'Se generaron {len(shipments)} registros de Shipment correctamente.'))
