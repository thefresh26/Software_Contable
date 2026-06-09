from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Inicializa el sistema: carga PUC colombiano y datos de prueba'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('========================================'))
        self.stdout.write(self.style.MIGRATE_HEADING('  Setup Inicial - ContaApp Colombia'))
        self.stdout.write(self.style.MIGRATE_HEADING('========================================'))
        self.stdout.write('')

        # 1. Aplicar migraciones pendientes
        self.stdout.write('1. Aplicando migraciones...')
        call_command('migrate', '--run-syncdb', verbosity=0)
        self.stdout.write(self.style.SUCCESS('   [OK] Migraciones aplicadas'))

        # 2. Cargar PUC
        self.stdout.write('2. Cargando Plan de Cuentas PUC Colombia...')
        from apps.contabilidad.models import CuentaPUC
        if CuentaPUC.objects.count() == 0:
            call_command('loaddata', 'puc_colombia', verbosity=0)
            total = CuentaPUC.objects.count()
            self.stdout.write(self.style.SUCCESS(f'   [OK] PUC cargado: {total} cuentas'))
        else:
            total = CuentaPUC.objects.count()
            self.stdout.write(self.style.WARNING(f'   [!]  PUC ya existe ({total} cuentas) - omitiendo'))

        # 3. Datos de prueba
        self.stdout.write('3. Cargando datos de prueba...')
        call_command('cargar_datos_prueba', verbosity=0)
        self.stdout.write(self.style.SUCCESS('   [OK] Datos de prueba listos'))

        # 4. Resumen
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('Resumen del sistema:'))
        self._resumen()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[*] Setup completado. El sistema esta listo.'))
        self.stdout.write('')
        self.stdout.write('  Backend:  http://localhost:8000')
        self.stdout.write('  Admin:    http://localhost:8000/admin')
        self.stdout.write('  Frontend: http://localhost:5173')
        self.stdout.write('  Usuario:  admin / (tu contrasena)')

    def _resumen(self):
        from apps.contabilidad.models import CuentaPUC
        from apps.terceros.models import Tercero
        from apps.inventario.models import Producto
        from apps.nomina.models import Empleado
        from apps.facturacion.models import TipoRetencion, Factura

        items = [
            ('Plan de Cuentas (PUC)',   CuentaPUC.objects.count()),
            ('Terceros',                Tercero.objects.count()),
            ('Productos',               Producto.objects.count()),
            ('Empleados',               Empleado.objects.count()),
            ('Tipos de Retencion',      TipoRetencion.objects.count()),
            ('Facturas',                Factura.objects.count()),
        ]
        for label, count in items:
            self.stdout.write(f'   {label:<30} {count:>5} registros')
