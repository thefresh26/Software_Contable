import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('facturacion', '0002_add_retenciones'),
        ('terceros', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CuentaPorCobrar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('factura', models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='cuenta_cobrar', to='facturacion.factura',
                )),
                ('tercero', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='cuentas_cobrar', to='terceros.tercero',
                )),
                ('valor_total', models.DecimalField(decimal_places=2, max_digits=15)),
                ('valor_pagado', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('valor_pendiente', models.DecimalField(decimal_places=2, max_digits=15)),
                ('fecha_vencimiento', models.DateField()),
                ('estado', models.CharField(
                    choices=[('pendiente', 'Pendiente'), ('parcial', 'Pago Parcial'),
                             ('pagada', 'Pagada'), ('vencida', 'Vencida')],
                    default='pendiente', max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'Cuenta por Cobrar', 'verbose_name_plural': 'Cuentas por Cobrar',
                     'ordering': ['fecha_vencimiento']},
        ),
        migrations.CreateModel(
            name='CuentaPorPagar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('factura', models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='cuenta_pagar', to='facturacion.factura',
                )),
                ('tercero', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='cuentas_pagar', to='terceros.tercero',
                )),
                ('valor_total', models.DecimalField(decimal_places=2, max_digits=15)),
                ('valor_pagado', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('valor_pendiente', models.DecimalField(decimal_places=2, max_digits=15)),
                ('fecha_vencimiento', models.DateField()),
                ('estado', models.CharField(
                    choices=[('pendiente', 'Pendiente'), ('parcial', 'Pago Parcial'),
                             ('pagada', 'Pagada'), ('vencida', 'Vencida')],
                    default='pendiente', max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'Cuenta por Pagar', 'verbose_name_plural': 'Cuentas por Pagar',
                     'ordering': ['fecha_vencimiento']},
        ),
        migrations.CreateModel(
            name='PagoRecibido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('cuenta_cobrar', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='pagos', to='cartera.cuentaporcobrar',
                )),
                ('fecha', models.DateField()),
                ('valor', models.DecimalField(decimal_places=2, max_digits=15)),
                ('medio_pago', models.CharField(
                    choices=[('efectivo', 'Efectivo'), ('transferencia', 'Transferencia'),
                             ('cheque', 'Cheque')],
                    max_length=20,
                )),
                ('referencia', models.CharField(blank=True, max_length=100)),
                ('observacion', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'Pago Recibido', 'ordering': ['-fecha']},
        ),
        migrations.CreateModel(
            name='PagoRealizado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('cuenta_pagar', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='pagos', to='cartera.cuentaporpagar',
                )),
                ('fecha', models.DateField()),
                ('valor', models.DecimalField(decimal_places=2, max_digits=15)),
                ('medio_pago', models.CharField(
                    choices=[('efectivo', 'Efectivo'), ('transferencia', 'Transferencia'),
                             ('cheque', 'Cheque')],
                    max_length=20,
                )),
                ('referencia', models.CharField(blank=True, max_length=100)),
                ('observacion', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'Pago Realizado', 'ordering': ['-fecha']},
        ),
    ]
