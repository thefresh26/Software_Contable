from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Carga datos de prueba realistas para el sistema contable'

    def handle(self, *args, **options):
        creados = {
            'terceros': self.cargar_terceros(),
            'categorias': self.cargar_categorias(),
            'productos': self.cargar_productos(),
            'empleados': self.cargar_empleados(),
            'retenciones': self.cargar_tipos_retencion(),
            'categorias_activos': self.cargar_categorias_activos(),
            'activos': self.cargar_activos(),
            'notificaciones': self.cargar_notificaciones(),
            'bancos': self.cargar_bancos(),
        }
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('[OK] Datos de prueba cargados:'))
        for k, v in creados.items():
            self.stdout.write(f'   {k}: {v[0]} creados, {v[1]} existentes')

    # ── Terceros ─────────────────────────────────────────────────────────────

    def cargar_terceros(self):
        from apps.terceros.models import Tercero
        datos = [
            {'tipo': 'cliente',    'tipo_persona': 'juridica', 'nombre': 'Supermercados La 14 S.A.',           'nit': '890900438-5', 'email': 'compras@la14.com',                'telefono': '6023456789', 'ciudad': 'Cali'},
            {'tipo': 'cliente',    'tipo_persona': 'juridica', 'nombre': 'Almacenes Éxito S.A.',                'nit': '890903708-3', 'email': 'proveedores@exito.com',           'telefono': '6044567890', 'ciudad': 'Medellín'},
            {'tipo': 'cliente',    'tipo_persona': 'natural',  'nombre': 'Carlos Andrés Gómez Pérez',           'nit': '1020304050-1', 'email': 'carlos.gomez@gmail.com',         'telefono': '3001234567', 'ciudad': 'Bogotá'},
            {'tipo': 'cliente',    'tipo_persona': 'juridica', 'nombre': 'Constructora Bolívar S.A.S.',         'nit': '800123456-7', 'email': 'pagos@constructorabolivar.com',   'telefono': '6015678901', 'ciudad': 'Bogotá'},
            {'tipo': 'cliente',    'tipo_persona': 'natural',  'nombre': 'María Elena Rodríguez Torres',        'nit': '52345678-9',  'email': 'maria.rodriguez@outlook.com',    'telefono': '3152345678', 'ciudad': 'Barranquilla'},
            {'tipo': 'proveedor',  'tipo_persona': 'juridica', 'nombre': 'Distribuidora Nacional S.A.S.',       'nit': '900234567-8', 'email': 'ventas@distnacional.com',         'telefono': '6012345678', 'ciudad': 'Bogotá'},
            {'tipo': 'proveedor',  'tipo_persona': 'juridica', 'nombre': 'Papelería y Suministros Ltda.',       'nit': '800567890-3', 'email': 'info@papeleria.com',              'telefono': '6044321098', 'ciudad': 'Medellín'},
            {'tipo': 'proveedor',  'tipo_persona': 'natural',  'nombre': 'Juan Pablo Martínez López',           'nit': '79876543-2',  'email': 'juanpablo@servicios.com',        'telefono': '3209876543', 'ciudad': 'Bogotá'},
            {'tipo': 'ambos',      'tipo_persona': 'juridica', 'nombre': 'Tecnología y Sistemas S.A.S.',        'nit': '900876543-1', 'email': 'contacto@tecsis.com',            'telefono': '6017654321', 'ciudad': 'Bogotá'},
            {'tipo': 'ambos',      'tipo_persona': 'juridica', 'nombre': 'Servicios Integrales del Caribe Ltda.', 'nit': '800432109-6', 'email': 'gerencia@sic.com',            'telefono': '6053456789', 'ciudad': 'Barranquilla'},
        ]
        creados = existentes = 0
        for d in datos:
            _, created = Tercero.objects.get_or_create(nit=d['nit'], defaults=d)
            if created:
                creados += 1
            else:
                existentes += 1
        return creados, existentes

    # ── Categorías ──────────────────────────────────────────────────────────

    def cargar_categorias(self):
        from apps.inventario.models import Categoria
        nombres = ['Electrónica', 'Papelería', 'Servicios', 'Muebles', 'Alimentos']
        creados = existentes = 0
        for nombre in nombres:
            _, created = Categoria.objects.get_or_create(nombre=nombre)
            if created:
                creados += 1
            else:
                existentes += 1
        return creados, existentes

    # ── Productos ────────────────────────────────────────────────────────────

    def cargar_productos(self):
        from apps.inventario.models import Producto, Categoria
        datos = [
            # (codigo, nombre, categoria, precio_compra, precio_venta, iva, stock, stock_min)
            ('ELEC-001', 'Computador Portátil HP 15',       'Electrónica', 1800000, 2500000, 19, 15, 3),
            ('ELEC-002', 'Monitor LG 24 pulgadas',          'Electrónica',  450000,  650000, 19, 20, 5),
            ('ELEC-003', 'Teclado y Mouse Inalámbrico',     'Electrónica',   85000,  130000, 19, 30, 10),
            ('ELEC-004', 'Impresora Epson L3150',           'Electrónica',  380000,  520000, 19,  8,  2),
            ('PAP-001',  'Resma Papel Carta 75g',           'Papelería',     12000,   18000, 19, 100, 20),
            ('PAP-002',  'Carpetas AZ Palanca',             'Papelería',      8500,   13000, 19,  50, 10),
            ('PAP-003',  'Bolígrafo Kilométrico x12',       'Papelería',      6000,    9500, 19,  80, 20),
            ('MUE-001',  'Silla Ejecutiva Ergonómica',      'Muebles',      280000,  420000, 19,  12,  3),
            ('MUE-002',  'Escritorio en L 1.80m',           'Muebles',      350000,  520000, 19,   6,  2),
            ('MUE-003',  'Archivador Metálico 4 Gavetas',   'Muebles',      420000,  620000, 19,   4,  1),
            ('SRV-001',  'Servicio Mantenimiento PC',       'Servicios',          0,   80000, 19, 999,  0),
            ('SRV-002',  'Consultoría Contable Hora',       'Servicios',          0,  150000, 19, 999,  0),
            ('ALI-001',  'Café Molido x500g',               'Alimentos',     12000,   18000,  0,  40, 10),
            ('ALI-002',  'Agua Cristal x24 und',            'Alimentos',     18000,   26000,  0,  25,  5),
            ('ALI-003',  'Azúcar x1kg',                     'Alimentos',      3500,    5500,  0,  30, 10),
        ]
        creados = existentes = 0
        for codigo, nombre, cat_nombre, pc, pv, iva, stock, stock_min in datos:
            cat = Categoria.objects.filter(nombre=cat_nombre).first()
            _, created = Producto.objects.get_or_create(
                codigo=codigo,
                defaults={
                    'nombre': nombre,
                    'categoria': cat,
                    'precio_compra': pc,
                    'precio_venta': pv,
                    'iva_porcentaje': iva,
                    'stock_actual': stock,
                    'stock_minimo': stock_min,
                    'unidad_medida': 'UND',
                    'activo': True,
                }
            )
            if created:
                creados += 1
            else:
                existentes += 1
        return creados, existentes

    # ── Empleados ────────────────────────────────────────────────────────────

    def cargar_empleados(self):
        from apps.nomina.models import Empleado
        import datetime
        datos = [
            ('Laura Milena Pérez Gómez',        '1090123456', 'Gerente General',        'Gerencia',        5000000, '2020-01-15', 'indefinido'),
            ('Andrés Felipe Martínez Cruz',      '1020456789', 'Contador',               'Contabilidad',    3500000, '2021-03-01', 'indefinido'),
            ('Sandra Milena Torres Ruiz',        '52789012',   'Auxiliar Contable',      'Contabilidad',    1500000, '2022-06-15', 'indefinido'),
            ('Carlos Eduardo Vargas López',      '79345678',   'Vendedor',               'Ventas',          1300000, '2023-01-10', 'fijo'),
            ('Juliana Andrea Ríos Herrera',      '1143567890', 'Asistente Administrativa', 'Administración', 1400000, '2023-08-01', 'indefinido'),
        ]
        creados = existentes = 0
        for nombre, cedula, cargo, depto, salario, ingreso, contrato in datos:
            _, created = Empleado.objects.get_or_create(
                cedula=cedula,
                defaults={
                    'nombre': nombre,
                    'cargo': cargo,
                    'departamento': depto,
                    'salario_base': salario,
                    'fecha_ingreso': datetime.date.fromisoformat(ingreso),
                    'tipo_contrato': contrato,
                    'activo': True,
                }
            )
            if created:
                creados += 1
            else:
                existentes += 1
        return creados, existentes

    # ── Tipos de retención ──────────────────────────────────────────────────

    def cargar_tipos_retencion(self):
        from apps.facturacion.models import TipoRetencion
        datos = [
            ('retefuente', 'ReteFuente Servicios 4%',      4.0),
            ('retefuente', 'ReteFuente Compras 2.5%',      2.5),
            ('retefuente', 'ReteFuente Honorarios 11%',    11.0),
            ('reteiva',    'ReteIVA 15%',                   15.0),
            ('reteica',    'ReteICA Bogotá 0.414%',          0.414),
            ('reteica',    'ReteICA Medellín 0.6%',          0.6),
            ('reteica',    'ReteICA Barranquilla 0.7%',      0.7),
        ]
        creados = existentes = 0
        for tipo, nombre, pct in datos:
            _, created = TipoRetencion.objects.get_or_create(
                nombre=nombre,
                defaults={'tipo': tipo, 'porcentaje': pct, 'activo': True}
            )
            if created:
                creados += 1
            else:
                existentes += 1
        return creados, existentes

    # ── Categorías de activos fijos ─────────────────────────────────────────

    def cargar_categorias_activos(self):
        from apps.activos.models import CategoriaActivo
        from apps.contabilidad.models import CuentaPUC
        datos = [
            {'nombre': 'Equipo de Cómputo',           'vida_util_años': 5,  'metodo': 'linea_recta',      'cuenta_activo': '1524', 'cuenta_dep_acum': '1592', 'cuenta_gasto_dep': '5160'},
            {'nombre': 'Muebles y Enseres',           'vida_util_años': 10, 'metodo': 'linea_recta',      'cuenta_activo': '1520', 'cuenta_dep_acum': '1592', 'cuenta_gasto_dep': '5160'},
            {'nombre': 'Vehículos',                   'vida_util_años': 5,  'metodo': 'reduccion_saldos', 'cuenta_activo': '1528', 'cuenta_dep_acum': '1592', 'cuenta_gasto_dep': '5160'},
            {'nombre': 'Maquinaria y Equipo',         'vida_util_años': 10, 'metodo': 'suma_digitos',     'cuenta_activo': '1516', 'cuenta_dep_acum': '1592', 'cuenta_gasto_dep': '5160'},
            {'nombre': 'Construcciones y Edificios',  'vida_util_años': 20, 'metodo': 'linea_recta',      'cuenta_activo': '1512', 'cuenta_dep_acum': '1592', 'cuenta_gasto_dep': '5160'},
        ]
        creados = existentes = 0
        for d in datos:
            _, created = CategoriaActivo.objects.get_or_create(
                nombre=d['nombre'],
                defaults={
                    'vida_util_años': d['vida_util_años'],
                    'metodo_depreciacion': d['metodo'],
                    'cuenta_activo': CuentaPUC.objects.filter(codigo=d['cuenta_activo']).first(),
                    'cuenta_depreciacion': CuentaPUC.objects.filter(codigo=d['cuenta_dep_acum']).first(),
                    'cuenta_gasto_depreciacion': CuentaPUC.objects.filter(codigo=d['cuenta_gasto_dep']).first(),
                }
            )
            if created:
                creados += 1
            else:
                existentes += 1
        return creados, existentes

    # ── Activos fijos ────────────────────────────────────────────────────────

    def cargar_activos(self):
        from apps.activos.models import CategoriaActivo, ActivoFijo
        import datetime
        datos = [
            {'codigo': 'ACT-001', 'nombre': 'Computador Portátil HP EliteBook', 'categoria': 'Equipo de Cómputo',          'fecha_compra': '2022-01-15', 'fecha_inicio_dep': '2022-02-01', 'valor_compra': 3500000,  'valor_residual':  350000, 'vida_util': 5,  'metodo': 'linea_recta'},
            {'codigo': 'ACT-002', 'nombre': 'Escritorio Ejecutivo',             'categoria': 'Muebles y Enseres',          'fecha_compra': '2021-06-01', 'fecha_inicio_dep': '2021-07-01', 'valor_compra': 1200000,  'valor_residual':  120000, 'vida_util': 10, 'metodo': 'linea_recta'},
            {'codigo': 'ACT-003', 'nombre': 'Toyota Hilux 2022',                'categoria': 'Vehículos',                  'fecha_compra': '2022-03-10', 'fecha_inicio_dep': '2022-04-01', 'valor_compra': 95000000, 'valor_residual': 9500000, 'vida_util': 5,  'metodo': 'reduccion_saldos'},
            {'codigo': 'ACT-004', 'nombre': 'Impresora Multifuncional Xerox',   'categoria': 'Equipo de Cómputo',          'fecha_compra': '2023-01-20', 'fecha_inicio_dep': '2023-02-01', 'valor_compra': 4200000,  'valor_residual':  420000, 'vida_util': 5,  'metodo': 'linea_recta'},
            {'codigo': 'ACT-005', 'nombre': 'Servidor Dell PowerEdge',          'categoria': 'Equipo de Cómputo',          'fecha_compra': '2021-09-01', 'fecha_inicio_dep': '2021-10-01', 'valor_compra': 12000000, 'valor_residual': 1200000, 'vida_util': 5,  'metodo': 'linea_recta'},
        ]
        creados = existentes = 0
        for i, d in enumerate(datos, start=1):
            cat = CategoriaActivo.objects.filter(nombre=d['categoria']).first()
            _, created = ActivoFijo.objects.get_or_create(
                codigo=d['codigo'],
                defaults={
                    'nombre': d['nombre'],
                    'categoria': cat,
                    'fecha_compra': datetime.date.fromisoformat(d['fecha_compra']),
                    'fecha_inicio_depreciacion': datetime.date.fromisoformat(d['fecha_inicio_dep']),
                    'valor_compra': d['valor_compra'],
                    'valor_residual': d['valor_residual'],
                    'vida_util_años': d['vida_util'],
                    'metodo_depreciacion': d['metodo'],
                    'valor_en_libros': d['valor_compra'],
                    'estado': 'activo',
                    'cuenta_activo': cat.cuenta_activo if cat else None,
                    'cuenta_depreciacion_acumulada': cat.cuenta_depreciacion if cat else None,
                    'cuenta_gasto_depreciacion': cat.cuenta_gasto_depreciacion if cat else None,
                }
            )
            if created:
                creados += 1
            else:
                existentes += 1
        return creados, existentes

    # ── Notificaciones ───────────────────────────────────────────────────────

    def cargar_notificaciones(self):
        from apps.core.models import Usuario
        from apps.notificaciones.models import Notificacion
        admin = Usuario.objects.filter(username='admin').first() or Usuario.objects.filter(is_superuser=True).first()
        if not admin:
            return 0, 0
        datos = [
            {'tipo': 'stock_bajo', 'titulo': '3 productos con stock bajo', 'mensaje': 'Revisa el inventario', 'prioridad': 'alta'},
            {'tipo': 'factura_vencer', 'titulo': '2 facturas por vencer', 'mensaje': 'Vencen en 3 días', 'prioridad': 'alta'},
            {'tipo': 'sistema', 'titulo': 'Bienvenido a ContaApp', 'mensaje': 'Tu sistema contable está listo', 'prioridad': 'baja'},
            {'tipo': 'nomina_pendiente', 'titulo': 'Nómina de junio pendiente', 'mensaje': '5 empleados por liquidar', 'prioridad': 'media'},
            {'tipo': 'activo_depreciado', 'titulo': 'Activo próximo a depreciarse', 'mensaje': 'Servidor Dell: quedan 3 meses', 'prioridad': 'media'},
        ]
        creados = existentes = 0
        for d in datos:
            _, created = Notificacion.objects.get_or_create(
                usuario=admin, tipo=d['tipo'], titulo=d['titulo'],
                defaults={'mensaje': d['mensaje'], 'prioridad': d['prioridad']},
            )
            if created:
                creados += 1
            else:
                existentes += 1
        return creados, existentes

    # ── Bancos ───────────────────────────────────────────────────────────────

    def cargar_bancos(self):
        from decimal import Decimal
        import datetime
        from apps.contabilidad.models import CuentaPUC
        from apps.bancos.models import CuentaBancaria, ExtractoBancario, MovimientoBancario

        cuentas_bancarias = [
            {
                'nombre': 'Bancolombia Cuenta Corriente',
                'banco': 'Bancolombia',
                'numero_cuenta': '123-456789-00',
                'tipo': 'corriente',
                'cuenta_contable': '111005',
                'cuenta_contable_nombre': 'Bancos Moneda Nacional',
                'saldo_inicial': 50000000,
            },
            {
                'nombre': 'Davivienda Cuenta de Ahorros',
                'banco': 'Davivienda',
                'numero_cuenta': '0012-3456-7890',
                'tipo': 'ahorros',
                'cuenta_contable': '111010',
                'cuenta_contable_nombre': 'Cuentas de Ahorro',
                'saldo_inicial': 15000000,
            },
        ]

        creados = existentes = 0
        cuentas_creadas = {}
        for d in cuentas_bancarias:
            cuenta_puc, _ = CuentaPUC.objects.get_or_create(
                codigo=d['cuenta_contable'],
                defaults={'nombre': d['cuenta_contable_nombre'], 'tipo': 'activo', 'nivel': 6},
            )
            cuenta, created = CuentaBancaria.objects.get_or_create(
                numero_cuenta=d['numero_cuenta'],
                defaults={
                    'nombre': d['nombre'],
                    'banco': d['banco'],
                    'tipo': d['tipo'],
                    'cuenta_contable': cuenta_puc,
                    'saldo_inicial': d['saldo_inicial'],
                    'saldo_actual': d['saldo_inicial'],
                },
            )
            cuentas_creadas[d['nombre']] = cuenta
            if created:
                creados += 1
            else:
                existentes += 1

        # Extracto de prueba con 10 movimientos
        movimientos_prueba = [
            {'fecha': '2026-06-02', 'descripcion': 'TRANSFERENCIA ALMACENES EXITO', 'tipo': 'credito', 'valor': 11424000},
            {'fecha': '2026-06-03', 'descripcion': 'PAGO DISTRIBUIDOR NACIONAL', 'tipo': 'debito', 'valor': 595000},
            {'fecha': '2026-06-05', 'descripcion': 'PAGO NOMINA JUNIO', 'tipo': 'debito', 'valor': 14000000},
            {'fecha': '2026-06-08', 'descripcion': 'TRANSFERENCIA CONSTRUCTORA BOLIVAR', 'tipo': 'credito', 'valor': 5000000},
            {'fecha': '2026-06-10', 'descripcion': 'COMISION BANCARIA', 'tipo': 'debito', 'valor': 35000},
            {'fecha': '2026-06-12', 'descripcion': 'PAGO SERVICIOS PUBLICOS', 'tipo': 'debito', 'valor': 450000},
            {'fecha': '2026-06-15', 'descripcion': 'ABONO CLIENTE CARLOS GOMEZ', 'tipo': 'credito', 'valor': 2000000},
            {'fecha': '2026-06-18', 'descripcion': 'CHEQUE 001 PAPELERIA SUMINISTROS', 'tipo': 'debito', 'valor': 280000},
            {'fecha': '2026-06-25', 'descripcion': 'INTERESES CUENTA CORRIENTE', 'tipo': 'credito', 'valor': 125000},
            {'fecha': '2026-06-28', 'descripcion': 'PAGO ARRIENDO OFICINA', 'tipo': 'debito', 'valor': 2500000},
        ]

        cuenta_bancolombia = cuentas_creadas['Bancolombia Cuenta Corriente']
        saldo_inicial = Decimal('50000000')
        if not cuenta_bancolombia.extractos.exists():
            saldo = saldo_inicial
            total_debitos = total_creditos = Decimal('0')
            filas = []
            for m in movimientos_prueba:
                valor = Decimal(str(m['valor']))
                if m['tipo'] == 'debito':
                    saldo -= valor
                    total_debitos += valor
                else:
                    saldo += valor
                    total_creditos += valor
                filas.append({**m, 'valor': valor, 'saldo': saldo})

            extracto = ExtractoBancario.objects.create(
                cuenta=cuenta_bancolombia,
                periodo_inicio=datetime.date(2026, 6, 1),
                periodo_fin=datetime.date(2026, 6, 30),
                saldo_inicial_extracto=saldo_inicial,
                saldo_final_extracto=filas[-1]['saldo'],
                total_debitos=total_debitos,
                total_creditos=total_creditos,
                archivo_original='extracto_junio_2026_prueba.xlsx',
            )
            for f in filas:
                MovimientoBancario.objects.create(
                    extracto=extracto,
                    fecha=datetime.date.fromisoformat(f['fecha']),
                    descripcion=f['descripcion'],
                    tipo=f['tipo'],
                    valor=f['valor'],
                    saldo=f['saldo'],
                )

        return creados, existentes
