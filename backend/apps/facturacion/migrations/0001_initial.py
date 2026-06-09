import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('terceros', '0001_initial'),
        ('inventario', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Factura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('numero', models.CharField(blank=True, max_length=20, unique=True)),
                ('tipo', models.CharField(
                    choices=[
                        ('FV', 'Factura de Venta'), ('FC', 'Factura de Compra'),
                        ('NC', 'Nota Crédito'), ('ND', 'Nota Débito'),
                    ],
                    max_length=2,
                )),
                ('tercero', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='facturas',
                    to='terceros.tercero',
                )),
                ('fecha', models.DateField()),
                ('fecha_vencimiento', models.DateField(blank=True, null=True)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('descuento', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('iva', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('estado', models.CharField(
                    choices=[('borrador', 'Borrador'), ('emitida', 'Emitida'),
                             ('anulada', 'Anulada')],
                    default='borrador',
                    max_length=20,
                )),
                ('observaciones', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Factura',
                'verbose_name_plural': 'Facturas',
                'ordering': ['-fecha', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DetalleFactura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('factura', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='detalles',
                    to='facturacion.factura',
                )),
                ('producto', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='inventario.producto',
                )),
                ('descripcion', models.CharField(max_length=200)),
                ('cantidad', models.DecimalField(decimal_places=2, max_digits=10)),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=15)),
                ('descuento_porcentaje', models.DecimalField(decimal_places=2, default=0,
                                                              max_digits=5)),
                ('iva_porcentaje', models.DecimalField(decimal_places=2, default=19,
                                                        max_digits=5)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('iva_valor', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
            ],
            options={
                'verbose_name': 'Detalle de Factura',
                'verbose_name_plural': 'Detalles de Factura',
            },
        ),
    ]
