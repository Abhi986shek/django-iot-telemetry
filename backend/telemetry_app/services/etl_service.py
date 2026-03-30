"""
telemetry_app.services.etl_service
-----------------------------------
Extract, Transform, Load (ETL) pipeline for industrial telemetry data.

Responsibilities:
    - Validate uploaded file type and size before processing.
    - Read CSV and Excel files into Pandas DataFrames.
    - Normalize heterogeneous column names from diverse hardware sources
      into the platform's unified schema (e.g. 'Voltage' -> 'vibration_frequency').
    - Execute the analytics engine against the normalized dataset.
    - Bulk-insert normalized records into the database atomically.
    - Write an audit entry to the IngestionLog table on every run.
"""
import os
import pandas as pd
import numpy as np
import logging
from django.db import transaction
from ..models import MachineNode, TelemetryRecord, IngestionLog
from .analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

COLUMN_MAP = {
    'operational_rpm': ['Capacity', 'RPM', 'Speed', 'C_Rate', 'C_rate'],
    'vibration_frequency': ['Voltage', 'Vibration', 'Hz', 'Vbat', 'Voltage_V'],
    'thermal_pressure': ['Current', 'Pressure', 'PSI', 'Current_A', 'Ibat'],
    'power_draw_kw': ['Energy', 'Power', 'kW', 'WhAccu', 'AhAccu'],
    'health_score': ['SOC', 'StateOfCharge', 'Health', 'Soc'],
    'shift_identifier': ['Shift', 'ShiftNo', 'Shift_No', 'Cycle', 'CycleNo'],
}


class ETLService:
    def process_upload(self, file_object, machine_id: str, shift_id: str = '') -> dict:
        """
        Reads, validates, normalizes, and persists an uploaded telemetry file.
        Handles both CSV and Excel formats. Maps diverse legacy column naming
        conventions to the platform's unified schema before database insertion.
        """
        self._validate_file(file_object)

        df = self._read_file(file_object)
        normalized_df = self._normalize_columns(df, shift_id)

        if normalized_df.empty:
            raise ValueError("No valid rows found after normalization. Check file format.")

        analytics = AnalyticsService.run_all(normalized_df)
        machine = self._get_or_create_machine(machine_id)
        count = self._bulk_persist(normalized_df, machine, analytics)

        IngestionLog.objects.create(
            machine=machine,
            file_name=file_object.name,
            records_processed=count,
            status='SUCCESS'
        )

        return {
            'machine_id': machine_id,
            'records_saved': count,
            'analytics_summary': analytics,
        }

    def _validate_file(self, file_object):
        allowed_extensions = ['.csv', '.xls', '.xlsx']
        ext = os.path.splitext(file_object.name)[1].lower()
        if ext not in allowed_extensions:
            raise ValueError(f"File type '{ext}' is not supported. Upload CSV or Excel files.")
        if file_object.size > 100 * 1024 * 1024:
            raise ValueError("File exceeds the 100 MB upload limit.")

    def _read_file(self, file_object) -> pd.DataFrame:
        ext = os.path.splitext(file_object.name)[1].lower()
        try:
            if ext == '.csv':
                return pd.read_csv(file_object)
            else:
                return pd.read_excel(file_object, engine='openpyxl')
        except Exception as e:
            raise ValueError(f"Could not parse file: {e}")

    def _normalize_columns(self, df: pd.DataFrame, shift_id: str) -> pd.DataFrame:
        normalized = pd.DataFrame()
        for target_col, source_names in COLUMN_MAP.items():
            for source in source_names:
                if source in df.columns:
                    normalized[target_col] = df[source]
                    break

        if 'shift_identifier' not in normalized.columns:
            normalized['shift_identifier'] = shift_id

        # Drop rows where core operational metrics are fully absent
        core_cols = [c for c in ['operational_rpm', 'vibration_frequency'] if c in normalized.columns]
        if core_cols:
            normalized.dropna(subset=core_cols, how='all', inplace=True)

        return normalized.reset_index(drop=True)

    def _get_or_create_machine(self, machine_id: str) -> MachineNode:
        machine, _ = MachineNode.objects.get_or_create(
            machine_id=machine_id,
            defaults={'location': 'Unspecified', 'description': f'Auto-registered node {machine_id}'}
        )
        return machine

    def _bulk_persist(self, df: pd.DataFrame, machine: MachineNode, analytics: dict) -> int:
        health_score = analytics.get('lifecycle', {}).get('computed_health_score', None)
        records = [
            TelemetryRecord(
                machine=machine,
                operational_rpm=row.get('operational_rpm'),
                vibration_frequency=row.get('vibration_frequency'),
                thermal_pressure=row.get('thermal_pressure'),
                power_draw_kw=row.get('power_draw_kw'),
                health_score=row.get('health_score') or health_score,
                shift_identifier=str(row.get('shift_identifier', '')),
            )
            for _, row in df.iterrows()
        ]

        with transaction.atomic():
            TelemetryRecord.objects.bulk_create(records, batch_size=2000)

        return len(records)
