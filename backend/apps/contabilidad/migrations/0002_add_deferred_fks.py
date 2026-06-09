import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Agrega los FK que no podían estar en 0001 por dependencias circulares:
      - AsientoContable.factura → facturacion.Factura
      - AsientoContable.nomina  → nomina.LiquidacionNomina
    """

    dependencies = [
        ('contabilidad', '0001_initial'),
        ('facturacion', '0001_initial'),
        ('nomina', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='asientocontable',
            name='factura',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='asiento',
                to='facturacion.factura',
            ),
        ),
        migrations.AddField(
            model_name='asientocontable',
            name='nomina',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='asiento',
                to='nomina.liquidacionnomina',
            ),
        ),
    ]
