"""
telemetry_app.models
--------------------
Defines the Django ORM models that map directly to database tables.

Models:
    MachineNode      -- A registered industrial machine or sensor node.
    TelemetryRecord  -- A single time-series reading from a MachineNode.
    IngestionLog     -- An audit record for every uploaded telemetry file.
"""
from django.db import models
from django.utils import timezone


class MachineNode(models.Model):
    """Represents a registered industrial machine/sensor node in the system."""
    machine_id = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    registered_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'machine_nodes'

    def __str__(self):
        return f"{self.machine_id} — {self.location}"


class TelemetryRecord(models.Model):
    """Stores a single time-series reading ingested from a machine node."""
    machine = models.ForeignKey(MachineNode, on_delete=models.CASCADE, related_name='records')
    operational_rpm = models.FloatField(null=True, blank=True)
    vibration_frequency = models.FloatField(null=True, blank=True)
    thermal_pressure = models.FloatField(null=True, blank=True)
    power_draw_kw = models.FloatField(null=True, blank=True)
    health_score = models.FloatField(null=True, blank=True)
    shift_identifier = models.CharField(max_length=100, blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'machine_telemetry'
        indexes = [
            models.Index(fields=['machine', '-recorded_at']),
        ]

    def __str__(self):
        return f"{self.machine.machine_id} @ {self.recorded_at}"


class IngestionLog(models.Model):
    """Audit trail for every data file uploaded to the platform."""
    machine = models.ForeignKey(MachineNode, on_delete=models.SET_NULL, null=True, related_name='ingestion_logs')
    file_name = models.CharField(max_length=255)
    records_processed = models.IntegerField(default=0)
    status = models.CharField(max_length=50, choices=[
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('PARTIAL', 'Partial'),
    ], default='SUCCESS')
    error_detail = models.TextField(blank=True)
    ingested_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'ingestion_logs'

    def __str__(self):
        return f"{self.file_name} — {self.status} ({self.ingested_at})"
