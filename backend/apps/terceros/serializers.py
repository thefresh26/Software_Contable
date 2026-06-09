from rest_framework import serializers
from .models import Tercero


class TerceroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tercero
        fields = '__all__'
        read_only_fields = ['id', 'empresa', 'created_at', 'updated_at']
