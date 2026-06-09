from django.core.management.base import BaseCommand
from apps.notificaciones.services import verificar_alertas


class Command(BaseCommand):
    help = 'Verifica todas las condiciones de alerta y envía notificaciones'

    def handle(self, *args, **options):
        self.stdout.write('Verificando alertas...')
        verificar_alertas()
        self.stdout.write(self.style.SUCCESS('Alertas verificadas'))
