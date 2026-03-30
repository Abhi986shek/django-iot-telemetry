from django.urls import path
from .controllers import dashboard, ingestion, administration

urlpatterns = [
    path('', dashboard.index, name='home'),
    path('dashboard/', dashboard.telemetry_dashboard, name='dashboard'),
    path('upload/', ingestion.upload_file, name='upload'),
    path('api/ingest/', ingestion.api_ingest, name='api_ingest'),
    path('api/machines/', dashboard.machine_list_api, name='machine_list_api'),
    path('api/telemetry/<str:machine_id>/', dashboard.telemetry_data_api, name='telemetry_data_api'),
    path('admin-panel/purge/', administration.purge_records, name='admin_purge'),
    path('admin-panel/logs/', administration.ingestion_logs, name='admin_logs'),
]
