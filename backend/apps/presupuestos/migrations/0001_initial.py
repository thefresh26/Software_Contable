import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('terceros', '0001_initial'),
        ('inventario', '0002_add_deferred_fks'),
        ('contabilidad', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cotizacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('numero', models.CharField(blank=True, max_length=20, unique=True)),
                ('tercero', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='cotizaciones',
                    to='terceros.tercero',
                )),
                ('fecha', models.DateField()),
                ('fecha_vencimiento', models.DateField()),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('iva', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('estado', models.CharField(
                    choices=[('borrador', 'Borrador'), ('enviada', 'Enviada'),
                             ('aprobada', 'Aprobada'), ('rechazada', 'Rechazada'),
                             ('vencida', 'Vencida')],
                    default='borrador', max_length=20,
                )),
                ('observaciones', models.TextField(blank=True)),
                ('terminos', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'Cotización', 'verbose_name_plural': 'Cotizaciones',
                     'ordering': ['-fecha', '-created_at']},
        ),
        migrations.CreateModel(
            name='DetalleCotizacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('cotizacion', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='detalles', to='presupuestos.cotizacion',
                )),
                ('producto', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='inventario.producto',
                )),
                ('descripcion', models.CharField(max_length=200)),
                ('cantidad', models.DecimalField(decimal_places=2, max_digits=10)),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=15)),
                ('iva_porcentaje', models.DecimalField(decimal_places=2, default=19, max_digits=5)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('iva_valor', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
            ],
        ),
        migrations.CreateModel(
            name='Presupuesto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('periodo_inicio', models.DateField()),
                ('periodo_fin', models.DateField()),
                ('estado', models.CharField(
                    choices=[('activo', 'Activo'), ('cerrado', 'Cerrado')],
                    default='activo', max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'Presupuesto', 'verbose_name_plural': 'Presupuestos',
                     'ordering': ['-periodo_inicio']},
        ),
        migrations.CreateModel(
            name='ItemPresupuesto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('presupuesto', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items', to='presupuestos.presupuesto',
                )),
                ('cuenta', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='contabilidad.cuentapuc',
                )),
                ('descripcion', models.CharField(max_length=200)),
                ('valor_presupuestado', models.DecimalField(decimal_places=2, max_digits=15)),
            ],
        ),
    ]
