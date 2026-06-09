from rest_framework import serializers
from .models import Usuario


class EmpresaActivaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    nit = serializers.CharField()


class UsuarioSerializer(serializers.ModelSerializer):
    empresa_activa = EmpresaActivaSerializer(read_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'empresa', 'nit_empresa', 'rol', 'is_active', 'empresa_activa']
        read_only_fields = ['id', 'empresa_activa']


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'first_name', 'last_name',
                  'empresa', 'nit_empresa', 'rol']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user
