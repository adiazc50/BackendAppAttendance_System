from django.db import connection
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import Asistente, Empleado, RegistroAsistencia
from .serializers import AsistenteSerializer, EmpleadoSerializer, RegistroAsistenciaSerializer
from django.db.models import Sum, F, ExpressionWrapper, fields, Case, When
from rest_framework import generics
import django_filters
from django_filters.rest_framework import DjangoFilterBackend



class AsistenteViewSet(viewsets.ModelViewSet):
    queryset = Asistente.objects.all()
    serializer_class = AsistenteSerializer

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer

class RegistroAsistenciaViewSet(viewsets.ModelViewSet):
    queryset = RegistroAsistencia.objects.all()
    serializer_class = RegistroAsistenciaSerializer

# Nueva vista para obtener las horas trabajadas por rango de fechas
class HorasTrabajadasPorRangoFecha(APIView):

    def get(self, request):
        # Obtener los parámetros de la URL
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')

        if not fecha_inicio or not fecha_fin:
            return Response({"error": "Faltan parámetros de fecha."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fecha_inicio = timezone.datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin = timezone.datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Formato de fecha inválido. Use AAAA-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Filtrar registros por rango de fecha
        registros = RegistroAsistencia.objects.filter(hora_ingreso__date__range=[fecha_inicio, fecha_fin])

        # Calcular la duración en horas
        registros = registros.annotate(
            duracion=ExpressionWrapper(
                Case(
                    When(hora_salida__isnull=True, then=timezone.now() - F('hora_ingreso')),
                    default=F('hora_salida') - F('hora_ingreso')
                ),
                output_field=fields.DurationField()
            )
        )

        # Convertir la duración a horas (en decimal)
        registros = registros.annotate(
            duracion_horas=ExpressionWrapper(
                F('duracion') / timedelta(hours=1),
                output_field=fields.FloatField()
            )
        )

        # Obtener información del asistente y su tipo de empleado
        registros = registros.select_related('asistente__empleado')

        total_horas_por_empleado = registros.values(
            'asistente__nombre_completo',
            'asistente__documento_identidad',
            'asistente__tipo_asistente',
            'asistente__empleado__tipo_empleado'
        ).annotate(
            total_horas=Sum('duracion_horas')
        )

        return Response(total_horas_por_empleado, status=status.HTTP_200_OK)
    
    
    
class RegistrosSinSalidaView(APIView):
    def get(self, request):
        # Filtrar registros con hora_salida null
        registros_sin_salida = RegistroAsistencia.objects.filter(hora_salida__isnull=True)
        
        # Serializar los datos
        serializer = RegistroAsistenciaSerializer(registros_sin_salida, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    
    
class TiempoTotalPorRangoFecha(APIView):
    def get(self, request):
        # Obtener los parámetros de la URL
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        empleado_id = request.GET.get('empleado_id', None)
        tipo_asistente = request.GET.get('tipo_asistente', None)
        area = request.GET.get('area', None)
        
        if not fecha_inicio or not fecha_fin:
            return Response({"error": "Faltan parámetros de fecha."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fecha_inicio = timezone.datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin = timezone.datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Formato de fecha inválido. Use AAAA-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Construir la consulta SQL
        query = """
            SELECT 
                asistente.nombre_completo,
                asistente.documento_identidad,
                asistente.tipo_asistente,
                SUM(TIMESTAMPDIFF(SECOND, registro.hora_ingreso, COALESCE(registro.hora_salida, NOW())) / 3600) AS total_horas
            FROM 
                registro_asistencia registro
            JOIN 
                asistente asistente ON registro.asistente_id = asistente.id
            WHERE 
                registro.hora_ingreso BETWEEN %s AND %s
        """

        params = [fecha_inicio, fecha_fin]

        if empleado_id:
            query += " AND asistente.id = %s"
            params.append(empleado_id)
        
        if tipo_asistente:
            query += " AND asistente.tipo_asistente = %s"
            params.append(tipo_asistente)
        
        if area:
            query += " AND asistente.area = %s"
            params.append(area)
        
        query += " GROUP BY asistente.nombre_completo, asistente.documento_identidad, asistente.tipo_asistente"

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        # Convertir los resultados en formato JSON
        resultados = [
            {
                'nombre_completo': row[0],
                'documento_identidad': row[1],
                'tipo_asistente': row[2],
                'total_horas': row[3],
            }
            for row in rows
        ]

        return Response(resultados, status=status.HTTP_200_OK)
    
    

class AsistenteListView(generics.ListAPIView):
    serializer_class = AsistenteSerializer

    def get_queryset(self):
        queryset = Asistente.objects.all()
        documento_identidad = self.request.query_params.get('documento_identidad', None)
        if documento_identidad is not None:
            queryset = queryset.filter(documento_identidad__icontains=documento_identidad)
        return queryset
    
    
    
class ConsultaPorDocumentoView(generics.ListAPIView):
    serializer_class = AsistenteSerializer

    def get_queryset(self):
        documento_identidad = self.kwargs['documento_identidad']
        return Asistente.objects.filter(documento_identidad=documento_identidad)
    
    
class UltimoRegistroPorDocumentoView(APIView):
    def get(self, request, documento_identidad):
        try:
            asistente = Asistente.objects.get(documento_identidad=documento_identidad)
            ultimo_registro = RegistroAsistencia.objects.filter(asistente=asistente).order_by('-hora_ingreso').first()

            if ultimo_registro:
                serializer = RegistroAsistenciaSerializer(ultimo_registro)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "No se encontraron registros para este documento."}, status=status.HTTP_404_NOT_FOUND)

        except Asistente.DoesNotExist:
            return Response({"detail": "Asistente no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, documento_identidad):
        try:
            asistente = Asistente.objects.get(documento_identidad=documento_identidad)
            ultimo_registro = RegistroAsistencia.objects.filter(asistente=asistente).order_by('-hora_ingreso').first()

            if ultimo_registro:
                serializer = RegistroAsistenciaSerializer(ultimo_registro, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"detail": "No se encontraron registros para este documento."}, status=status.HTTP_404_NOT_FOUND)

        except Asistente.DoesNotExist:
            return Response({"detail": "Asistente no encontrado."}, status=status.HTTP_404_NOT_FOUND)