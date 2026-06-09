import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Crea Categoria, Producto y MovimientoInventario SIN los FK circulares:
      - Producto.cuenta_inventario  (→ contabilidad.CuentaPUC)
      - MovimientoInventario.factura (→ facturacion.Factura)
    Esos campos se agregan en 0002_add_deferred_fks una vez que facturacion
    y contabilidad ya existen.
    """

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Categoría',
                'verbose_name_plural': 'Categorías',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=50, unique=True)),
                ('nombre', models.CharField(max_length=200)),
                ('descripcion', models.TextField(blank=True)),
                ('categoria', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='inventario.categoria',
                )),
                ('precio_compra', models.DecimalField(decimal_places=2, default=0,
                                                       max_digits=15)),
                ('precio_venta', models.DecimalField(decimal_places=2, default=0,
                                                      max_digits=15)),
                ('iva_porcentaje', models.DecimalField(decimal_places=2, default=19,
                                                        max_digits=5)),
                ('stock_actual', models.IntegerField(default=0)),
                ('stock_minimo', models.IntegerField(default=5)),
                ('unidad_medida', models.CharField(default='UND', max_length=20)),
                ('activo', models.BooleanField(default=True)),
                # cuenta_inventario agregado en 0002_add_deferred_fks
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Producto',
                'verbose_name_plural': 'Productos',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='MovimientoInventario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('producto', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='movimientos',
                    to='inventario.producto',
                )),
                ('tipo', models.CharField(
                    choices=[('entrada', 'Entrada'), ('salida', 'Salida'),
                             ('ajuste', 'Ajuste')],
                    max_length=20,
                )),
                ('cantidad', models.IntegerField()),
                ('stock_anterior', models.IntegerField()),
                ('stock_nuevo', models.IntegerField()),
                ('motivo', models.CharField(max_length=200)),
                # factura agregado en 0002_add_deferred_fks
                ('fecha', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Movimiento de Inventario',
                'verbose_name_plural': 'Movimientos de Inventario',
                'ordering': ['-fecha'],
            },
        ),
    ]
