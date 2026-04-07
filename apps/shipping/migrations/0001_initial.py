from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Shipment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_id", models.PositiveBigIntegerField(db_index=True)),
                ("payment_id", models.PositiveBigIntegerField(db_index=True)),
                ("user_id", models.PositiveBigIntegerField(db_index=True)),
                ("delivery_address", models.TextField()),
                ("tracking_guide", models.CharField(db_index=True, max_length=32, unique=True)),
                ("courier", models.CharField(default="Paqueteria Demo", max_length=100)),
                ("estimated_delivery_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PREPARING", "Preparando"),
                            ("IN_TRANSIT", "En transito"),
                            ("DELIVERED", "Entregado"),
                        ],
                        default="PREPARING",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        )
    ]
