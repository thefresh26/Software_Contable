from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='rol',
            field=models.CharField(
                choices=[
                    ('admin', 'Administrador'), ('contador', 'Contador'),
                    ('auxiliar', 'Auxiliar Contable'), ('gerente', 'Gerente'),
                    ('vendedor', 'Vendedor'),
                ],
                default='auxiliar',
                max_length=20,
            ),
        ),
    ]
