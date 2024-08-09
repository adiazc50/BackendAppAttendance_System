from django.urls import include, path
from .views import AsistenteListView, AsistenteViewSet, ConsultaPorDocumentoView, EmpleadoViewSet, RegistroAsistenciaViewSet, HorasTrabajadasPorRangoFecha, RegistrosSinSalidaView, TiempoTotalPorRangoFecha, UltimoRegistroPorDocumentoView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'asistentes', AsistenteViewSet)
router.register(r'empleados', EmpleadoViewSet)
router.register(r'registros', RegistroAsistenciaViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('horas-trabajadas/', HorasTrabajadasPorRangoFecha.as_view(), name='horas_trabajadas_por_rango_fecha'),
    path('registros-sin-salida/', RegistrosSinSalidaView.as_view(), name='registros-sin-salida'),
    path('tiempo-total-por-rango/', TiempoTotalPorRangoFecha.as_view(), name='tiempo_total_por_rango'),
    path('asistentes/', AsistenteViewSet.as_view({'get': 'list'}), name='asistente-list'),
    path('asistentes/consultapordocumento/<str:documento_identidad>/', ConsultaPorDocumentoView.as_view(), name='consulta-por-documento'),
    path('registros/ultimo/<str:documento_identidad>/', UltimoRegistroPorDocumentoView.as_view(), name='ultimo-registro-por-documento'),
]
