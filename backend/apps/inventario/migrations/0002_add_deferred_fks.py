import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Agrega los FK que no podían estar en 0001 por dependencias circulares:
      - Producto.cuenta_inventario → contabilidad.CuentaPUC
      - MovimientoInventario.factura → facturacion.Factura
    """

    dependencies = [
        ('inventario', '0001_initial'),
        ('contabilidad', '0001_initial'),
        ('facturacion', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='cuenta_inventario',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='productos_inventario',
                to='contabilidad.cuentapuc',
            ),
        ),
        migrations.AddField(
            model_name='movimientoinventario',
            name='factura',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='movimientos_inventario',
                to='facturacion.factura',
            ),
        ),
    ]
