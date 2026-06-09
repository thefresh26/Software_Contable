import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0002_add_deferred_fks'),
    ]

    operations = [
        migrations.CreateModel(
            name='CentroCosto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=20, unique=True)),
                ('nombre', models.CharField(max_length=200)),
                ('descripcion', models.TextField(blank=True)),
                ('activo', models.BooleanField(default=True)),
                ('padre', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='hijos',
                    to='contabilidad.centrocosto',
                )),
            ],
            options={
                'verbose_name': 'Centro de Costo',
                'verbose_name_plural': 'Centros de Costo',
                'ordering': ['codigo'],
            },
        ),
    ]
