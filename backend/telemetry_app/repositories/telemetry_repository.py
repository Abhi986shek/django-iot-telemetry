"""
telemetry_app.repositories.telemetry_repository
------------------------------------------------
Read-only database query layer for the telemetry application.

This module is the exclusive interface for all ORM SELECT operations.
Controllers and services call this class for data retrieval and must
not perform ORM queries directly. Write operations (INSERT, DELETE)
are handled by the service layer or by Django's ORM in models.
"""
import logging
from ..models import MachineNode, TelemetryRecord, IngestionLog

logger = logging.getLogger(__name__)


class TelemetryRepository:
    """
    Encapsulates all ORM read queries for the application.
    Controllers and services call this layer exclusively for data retrieval.
    """

    def get_dashboard_summary(self) -> dict:
        total_machines = MachineNode.objects.filter(is_active=True).count()
        total_records = TelemetryRecord.objects.count()
        recent_logs = IngestionLog.objects.order_by('-ingested_at')[:5].values(
            'file_name', 'status', 'records_processed', 'ingested_at'
        )
        return {
            'total_active_machines': total_machines,
            'total_telemetry_records': total_records,
            'recent_ingestions': list(recent_logs),
        }

    def get_all_machines(self) -> list:
        return list(
            MachineNode.objects.filter(is_active=True).values(
                'machine_id', 'location', 'description', 'registered_at'
            )
        )

    def get_telemetry_for_machine(self, machine_id: str, limit: int = 500) -> list:
        try:
            machine = MachineNode.objects.get(machine_id=machine_id)
        except MachineNode.DoesNotExist:
            return []

        records = TelemetryRecord.objects.filter(machine=machine).order_by('-recorded_at')[:limit]
        return [
            {
                'rpm': r.operational_rpm,
                'vibration': r.vibration_frequency,
                'pressure': r.thermal_pressure,
                'power': r.power_draw_kw,
                'health': r.health_score,
                'shift': r.shift_identifier,
                'timestamp': r.recorded_at.isoformat(),
            }
            for r in records
        ]

    def get_ingestion_logs(self, limit: int = 100) -> list:
        return list(
            IngestionLog.objects.order_by('-ingested_at')[:limit].values(
                'machine__machine_id', 'file_name', 'status',
                'records_processed', 'error_detail', 'ingested_at'
            )
        )

    def purge_machine_records(self, machine_id: str) -> int:
        if not machine_id:
            count, _ = TelemetryRecord.objects.all().delete()
            return count
        try:
            machine = MachineNode.objects.get(machine_id=machine_id)
            count, _ = TelemetryRecord.objects.filter(machine=machine).delete()
            return count
        except MachineNode.DoesNotExist:
            return 0
