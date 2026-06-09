import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Agrega TipoRetencion y RetencionFactura.
    TipoRetencion.cuenta_contable → contabilidad.CuentaPUC (nullable, no circular)
    """

    dependencies = [
        ('facturacion', '0001_initial'),
        ('contabilidad', '0002_add_deferred_fks'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoRetencion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(
                    choices=[('reteiva', 'ReteIVA'), ('reteica', 'ReteICA'),
                             ('retefuente', 'ReteFuente')],
                    max_length=20,
                )),
                ('nombre', models.CharField(max_length=200)),
                ('porcentaje', models.DecimalField(decimal_places=2, max_digits=5)),
                ('cuenta_contable', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='tipos_retencion',
                    to='contabilidad.cuentapuc',
                )),
                ('activo', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Tipo de Retención',
                'verbose_name_plural': 'Tipos de Retención',
                'ordering': ['tipo', 'nombre'],
            },
        ),
        migrations.CreateModel(
            name='RetencionFactura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('factura', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='retenciones',
                    to='facturacion.factura',
                )),
                ('tipo_retencion', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='facturacion.tiporetencion',
                )),
                ('base', models.DecimalField(decimal_places=2, max_digits=15)),
                ('porcentaje', models.DecimalField(decimal_places=2, max_digits=5)),
                ('valor', models.DecimalField(decimal_places=2, max_digits=15)),
            ],
            options={
                'verbose_name': 'Retención de Factura',
                'verbose_name_plural': 'Retenciones de Factura',
            },
        ),
    ]
