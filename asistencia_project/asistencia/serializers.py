from rest_framework import serializers
from .models import Asistente, Empleado, RegistroAsistencia

class AsistenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asistente
        fields = '__all__'

class RegistroAsistenciaSerializer(serializers.ModelSerializer):
    asistente = AsistenteSerializer()

    class Meta:
        model = RegistroAsistencia
        fields = '__all__'

    def create(self, validated_data):
        asistente_data = validated_data.pop('asistente')
        asistente, created = Asistente.objects.get_or_create(**asistente_data)
        registro_asistencia = RegistroAsistencia.objects.create(asistente=asistente, **validated_data)
        return registro_asistencia

class EmpleadoSerializer(serializers.ModelSerializer):
    asistente = AsistenteSerializer()

    class Meta:
        model = Empleado
        fields = ['id', 'asistente', 'tipo_empleado']

    def create(self, validated_data):
        asistente_data = validated_data.pop('asistente')
        asistente = Asistente.objects.create(**asistente_data)
        empleado = Empleado.objects.create(asistente=asistente, **validated_data)
        return empleado

