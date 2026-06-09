import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Empleado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('cedula', models.CharField(max_length=20, unique=True)),
                ('cargo', models.CharField(max_length=100)),
                ('departamento', models.CharField(blank=True, max_length=100)),
                ('salario_base', models.DecimalField(decimal_places=2, max_digits=15)),
                ('fecha_ingreso', models.DateField()),
                ('tipo_contrato', models.CharField(
                    choices=[('indefinido', 'Indefinido'), ('fijo', 'Término fijo'),
                             ('obra_labor', 'Obra o labor')],
                    default='indefinido',
                    max_length=20,
                )),
                ('activo', models.BooleanField(default=True)),
                ('cuenta_bancaria', models.CharField(blank=True, max_length=30)),
                ('banco', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Empleado',
                'verbose_name_plural': 'Empleados',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='LiquidacionNomina',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('empleado', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='liquidaciones',
                    to='nomina.empleado',
                )),
                ('periodo_inicio', models.DateField()),
                ('periodo_fin', models.DateField()),
                ('salario_base', models.DecimalField(decimal_places=2, max_digits=15)),
                ('auxilio_transporte', models.DecimalField(decimal_places=2, default=0,
                                                           max_digits=15)),
                ('horas_extra_diurnas', models.DecimalField(decimal_places=2, default=0,
                                                             max_digits=10)),
                ('valor_horas_extra_diurnas', models.DecimalField(decimal_places=2, default=0,
                                                                   max_digits=15)),
                ('horas_extra_nocturnas', models.DecimalField(decimal_places=2, default=0,
                                                               max_digits=10)),
                ('valor_horas_extra_nocturnas', models.DecimalField(decimal_places=2, default=0,
                                                                     max_digits=15)),
                ('bonificaciones', models.DecimalField(decimal_places=2, default=0,
                                                        max_digits=15)),
                ('total_devengado', models.DecimalField(decimal_places=2, max_digits=15)),
                ('salud_empleado', models.DecimalField(decimal_places=2, max_digits=15)),
                ('pension_empleado', models.DecimalField(decimal_places=2, max_digits=15)),
                ('retencion_fuente', models.DecimalField(decimal_places=2, default=0,
                                                          max_digits=15)),
                ('otras_deducciones', models.DecimalField(decimal_places=2, default=0,
                                                           max_digits=15)),
                ('total_deducido', models.DecimalField(decimal_places=2, max_digits=15)),
                ('salud_empresa', models.DecimalField(decimal_places=2, max_digits=15)),
                ('pension_empresa', models.DecimalField(decimal_places=2, max_digits=15)),
                ('arl', models.DecimalField(decimal_places=2, max_digits=15)),
                ('caja_compensacion', models.DecimalField(decimal_places=2, max_digits=15)),
                ('sena', models.DecimalField(decimal_places=2, max_digits=15)),
                ('icbf', models.DecimalField(decimal_places=2, max_digits=15)),
                ('neto_pagar', models.DecimalField(decimal_places=2, max_digits=15)),
                ('estado', models.CharField(
                    choices=[('liquidada', 'Liquidada'), ('pagada', 'Pagada')],
                    default='liquidada',
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Liquidación de Nómina',
                'verbose_name_plural': 'Liquidaciones de Nómina',
                'ordering': ['-periodo_fin'],
            },
        ),
    ]
