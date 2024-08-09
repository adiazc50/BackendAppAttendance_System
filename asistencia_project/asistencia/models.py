from django.db import models

class Asistente(models.Model):
    TIPO_ASISTENTE = [
        ('empleado', 'Empleado'),
        ('proveedor', 'Proveedor'),
        ('invitado', 'Invitado'),
    ]

    nombre_completo = models.CharField(max_length=255)
    documento_identidad = models.CharField(max_length=50)
    tipo_asistente = models.CharField(max_length=10, choices=TIPO_ASISTENTE)

    def __str__(self):
        return self.nombre_completo

class Empleado(models.Model):
    TIPO_EMPLEADO = [
        ('administrativo', 'Administrativo'),
        ('operativo', 'Operativo'),
    ]

    asistente = models.OneToOneField(Asistente, on_delete=models.CASCADE)
    tipo_empleado = models.CharField(max_length=20, choices=TIPO_EMPLEADO)

class RegistroAsistencia(models.Model):
    asistente = models.ForeignKey(Asistente, on_delete=models.CASCADE)
    hora_ingreso = models.DateTimeField()
    hora_salida = models.DateTimeField(null=True, blank=True)
    motivo_antes_16 = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'asistencia_registroasistencia'  # Nombre correcto de la tabla

    def __str__(self):
        return f'{self.asistente.nombre_completo} - {self.hora_ingreso}'
