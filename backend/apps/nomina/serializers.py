from decimal import Decimal
import datetime
from rest_framework import serializers
from .models import Empleado, LiquidacionNomina


class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class LiquidacionNominaSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source='empleado.nombre', read_only=True)

    class Meta:
        model = LiquidacionNomina
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at',
            'salario_base', 'auxilio_transporte',
            'valor_horas_extra_diurnas', 'valor_horas_extra_nocturnas',
            'total_devengado', 'salud_empleado', 'pension_empleado',
            'total_deducido', 'salud_empresa', 'pension_empresa',
            'arl', 'caja_compensacion', 'sena', 'icbf', 'neto_pagar',
        ]


class LiquidarNominaSerializer(serializers.Serializer):
    empleado = serializers.PrimaryKeyRelatedField(queryset=Empleado.objects.filter(activo=True))
    periodo_inicio = serializers.DateField()
    periodo_fin = serializers.DateField()
    bonificaciones = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'))
    horas_extra_diurnas = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    horas_extra_nocturnas = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    retencion_fuente = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'))
    otras_deducciones = serializers.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'))

    def validate(self, data):
        if data['periodo_fin'] < data['periodo_inicio']:
            raise serializers.ValidationError('periodo_fin debe ser >= periodo_inicio')
        return data
