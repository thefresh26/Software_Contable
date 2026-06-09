from django.db import migrations


def asignar_empresa_defecto(apps, schema_editor):
    Empresa = apps.get_model('empresas', 'Empresa')
    UsuarioEmpresa = apps.get_model('empresas', 'UsuarioEmpresa')
    Usuario = apps.get_model('core', 'Usuario')

    admin = Usuario.objects.filter(is_superuser=True).first()
    if not admin:
        return

    empresa, _ = Empresa.objects.get_or_create(
        nit='900000001-0',
        defaults={
            'nombre': 'Mi Empresa S.A.S.',
            'razon_social': 'Mi Empresa S.A.S.',
            'ciudad': 'Barranquilla',
            'regimen': 'comun',
        },
    )

    admin.empresa_activa = empresa
    admin.save()

    UsuarioEmpresa.objects.get_or_create(
        usuario=admin,
        empresa=empresa,
        defaults={'rol': 'admin'},
    )

    for usuario in Usuario.objects.exclude(pk=admin.pk):
        if not usuario.empresa_activa_id:
            usuario.empresa_activa = empresa
            usuario.save()
        UsuarioEmpresa.objects.get_or_create(
            usuario=usuario,
            empresa=empresa,
            defaults={'rol': 'auxiliar'},
        )

    modelos = [
        ('terceros', 'Tercero'),
        ('inventario', 'Categoria'),
        ('inventario', 'Producto'),
        ('facturacion', 'Factura'),
        ('contabilidad', 'CuentaPUC'),
        ('contabilidad', 'AsientoContable'),
        ('contabilidad', 'CentroCosto'),
        ('nomina', 'Empleado'),
        ('nomina', 'LiquidacionNomina'),
        ('presupuestos', 'Cotizacion'),
        ('presupuestos', 'Presupuesto'),
        ('cartera', 'CuentaPorCobrar'),
        ('cartera', 'CuentaPorPagar'),
        ('activos', 'ActivoFijo'),
        ('activos', 'CategoriaActivo'),
        ('bancos', 'CuentaBancaria'),
        ('bancos', 'ExtractoBancario'),
        ('bancos', 'ConciliacionBancaria'),
        ('notificaciones', 'Notificacion'),
    ]
    for app_label, model_name in modelos:
        try:
            Model = apps.get_model(app_label, model_name)
            Model.objects.filter(empresa__isnull=True).update(empresa=empresa)
        except Exception:
            pass


def revertir(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('empresas', '0001_initial'),
        ('core', '0004_usuario_empresa_activa'),
        ('terceros', '0002_tercero_empresa_alter_tercero_nit_and_more'),
        ('inventario', '0003_categoria_empresa_producto_empresa_and_more'),
        ('facturacion', '0004_factura_empresa_alter_factura_numero_and_more'),
        ('contabilidad', '0005_asientocontable_empresa_centrocosto_empresa_and_more'),
        ('nomina', '0003_empleado_empresa_liquidacionnomina_empresa_and_more'),
        ('presupuestos', '0002_cotizacion_empresa_presupuesto_empresa_and_more'),
        ('cartera', '0003_cuentaporcobrar_empresa_cuentaporpagar_empresa'),
        ('activos', '0002_activofijo_empresa_categoriaactivo_empresa_and_more'),
        ('bancos', '0002_conciliacionbancaria_empresa_cuentabancaria_empresa_and_more'),
        ('notificaciones', '0002_notificacion_empresa'),
    ]

    operations = [
        migrations.RunPython(asignar_empresa_defecto, revertir),
    ]
