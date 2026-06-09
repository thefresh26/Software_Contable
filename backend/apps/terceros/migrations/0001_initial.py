from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Tercero',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(
                    choices=[('cliente', 'Cliente'), ('proveedor', 'Proveedor'),
                             ('ambos', 'Ambos')],
                    max_length=20,
                )),
                ('tipo_persona', models.CharField(
                    choices=[('natural', 'Persona Natural'), ('juridica', 'Persona Jurídica')],
                    default='natural',
                    max_length=20,
                )),
                ('nombre', models.CharField(max_length=200)),
                ('nit', models.CharField(max_length=20, unique=True)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('telefono', models.CharField(blank=True, max_length=20)),
                ('direccion', models.TextField(blank=True)),
                ('ciudad', models.CharField(blank=True, max_length=100)),
                ('activo', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Tercero',
                'verbose_name_plural': 'Terceros',
                'ordering': ['nombre'],
            },
        ),
    ]
