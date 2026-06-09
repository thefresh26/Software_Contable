import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0002_add_retenciones'),
        ('inventario', '0002_add_deferred_fks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='detallefactura',
            name='producto',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='inventario.producto',
            ),
        ),
    ]
