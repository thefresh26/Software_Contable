import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0003_add_centrocosto'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimientocontable',
            name='centro_costo',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='movimientos',
                to='contabilidad.centrocosto',
            ),
        ),
    ]
