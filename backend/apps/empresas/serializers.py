from rest_framework import serializers
from .models import Empresa, UsuarioEmpresa


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'
        read_only_fields = ['created_at']


class UsuarioEmpresaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    empresa_nombre = serializers.CharField(source='empresa.nombre', read_only=True)

    class Meta:
        model = UsuarioEmpresa
        fields = ['id', 'usuario', 'usuario_nombre', 'usuario_username',
                  'empresa', 'empresa_nombre', 'rol', 'activo', 'fecha_ingreso']
        read_only_fields = ['fecha_ingreso']


class EmpresaConRolSerializer(serializers.ModelSerializer):
    """Empresa con el rol que tiene el usuario autenticado en ella."""
    rol = serializers.SerializerMethodField()
    es_activa = serializers.SerializerMethodField()

    class Meta:
        model = Empresa
        fields = ['id', 'nombre', 'nit', 'razon_social', 'ciudad', 'regimen', 'activa', 'rol', 'es_activa']

    def get_rol(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        ue = obj.usuarios.filter(usuario=request.user, activo=True).first()
        return ue.rol if ue else None

    def get_es_activa(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        return request.user.empresa_activa_id == obj.id
