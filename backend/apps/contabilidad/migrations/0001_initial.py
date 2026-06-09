import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Crea CuentaPUC, AsientoContable y MovimientoContable SIN los FK circulares:
      - AsientoContable.factura  (→ facturacion.Factura)
      - AsientoContable.nomina   (→ nomina.LiquidacionNomina)
    Esos campos se agregan en 0002_add_deferred_fks.
    """

    initial = True

    dependencies = [
        ('nomina', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CuentaPUC',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=10, unique=True)),
                ('nombre', models.CharField(max_length=200)),
                ('tipo', models.CharField(
                    choices=[
                        ('activo', 'Activo'), ('pasivo', 'Pasivo'),
                        ('patrimonio', 'Patrimonio'), ('ingreso', 'Ingreso'),
                        ('gasto', 'Gasto'), ('costo', 'Costo'),
                    ],
                    max_length=20,
                )),
                ('padre', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='hijos',
                    to='contabilidad.cuentapuc',
                )),
                ('nivel', models.IntegerField()),
                ('activa', models.BooleanField(default=True)),
                ('permite_movimiento', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Cuenta PUC',
                'verbose_name_plural': 'Cuentas PUC',
                'ordering': ['codigo'],
            },
        ),
        migrations.CreateModel(
            name='AsientoContable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('descripcion', models.TextField()),
                # factura y nomina se agregan en 0002_add_deferred_fks
                ('es_manual', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Asiento Contable',
                'verbose_name_plural': 'Asientos Contables',
                'ordering': ['-fecha', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MovimientoContable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('asiento', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='movimientos',
                    to='contabilidad.asientocontable',
                )),
                ('cuenta', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='movimientos',
                    to='contabilidad.cuentapuc',
                )),
                ('descripcion', models.CharField(blank=True, max_length=200)),
                ('debito', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('credito', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
            ],
            options={
                'verbose_name': 'Movimiento Contable',
                'verbose_name_plural': 'Movimientos Contables',
            },
        ),
    ]
