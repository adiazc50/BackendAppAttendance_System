# Generated by Django 5.1 on 2024-08-08 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asistencia', '0002_alter_asistente_documento_identidad'),
    ]

    operations = [
        migrations.AlterField(
            model_name='empleado',
            name='tipo_empleado',
            field=models.CharField(choices=[('administrativo', 'Administrativo'), ('operativo', 'Operativo')], max_length=20),
        ),
    ]
