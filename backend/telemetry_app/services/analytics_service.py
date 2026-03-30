"""
telemetry_app.services.analytics_service
-----------------------------------------
Stateless analytics engine for industrial IoT telemetry data.

Each method is a pure function: it accepts a normalized Pandas DataFrame
and returns a structured result dictionary. There are no Django ORM calls,
no HTTP interactions, and no side effects within this module.

Algorithms:
    stress_test_analysis       -- Cumulative RPM load integration and peak detection.
    environmental_analysis     -- Thermal gradient trends and pressure anomaly flagging.
    vibration_shock_analysis   -- Variance-based bearing and shaft degradation detection.
    lifecycle_degradation_analysis -- Health score estimation from operational shift data.
    run_all                    -- Executes all algorithms and returns a consolidated report.
"""
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Stateless analytics engine. Each method accepts a normalized DataFrame
    and returns a structured result dictionary. No Django ORM calls exist here.
    """

    @staticmethod
    def stress_test_analysis(df: pd.DataFrame) -> dict:
        """
        Computes cumulative operational load using numerical integration over RPM readings.
        Identifies peak load events exceeding safe operational thresholds.
        """
        col = 'operational_rpm'
        if col not in df.columns or df[col].dropna().empty:
            return {}

        series = df[col].dropna()
        cumulative_load = float(np.trapz(series.values))
        peak_rpm = float(series.max())
        sustained_overload_count = int((series > series.quantile(0.95)).sum())

        return {
            'cumulative_operational_load': round(cumulative_load, 4),
            'peak_rpm_observed': round(peak_rpm, 4),
            'high_stress_events': sustained_overload_count,
        }

    @staticmethod
    def environmental_analysis(df: pd.DataFrame) -> dict:
        """
        Evaluates thermal gradient trends and pressure anomalies. Flags shifts
        where temperature rate-of-change exceeds acceptable engineering tolerances.
        """
        col = 'thermal_pressure'
        if col not in df.columns or df[col].dropna().empty:
            return {}

        series = df[col].dropna()
        gradient = float(series.diff().mean())
        critical_count = int((series > series.mean() + 2 * series.std()).sum())

        return {
            'mean_thermal_gradient': round(gradient, 6),
            'critical_thermal_events': critical_count,
            'max_pressure_reading': float(series.max()),
        }

    @staticmethod
    def vibration_shock_analysis(df: pd.DataFrame) -> dict:
        """
        Analyzes vibration frequency variance to detect mechanical looseness or
        imbalance patterns indicating bearing or shaft degradation.
        """
        col = 'vibration_frequency'
        if col not in df.columns or df[col].dropna().empty:
            return {}

        series = df[col].dropna()
        variance = float(series.var())
        std_dev = float(series.std())
        shock_events = int((series.diff().abs() > 3 * std_dev).sum())

        return {
            'vibration_variance': round(variance, 6),
            'standard_deviation': round(std_dev, 6),
            'shock_impulse_events': shock_events,
        }

    @staticmethod
    def lifecycle_degradation_analysis(df: pd.DataFrame) -> dict:
        """
        Estimates machine health degradation based on operational shift count and
        cumulative power draw. Outputs a normalized health score between 0 and 100.
        """
        power_col = 'power_draw_kw'
        shift_col = 'shift_identifier'

        total_shifts = df[shift_col].nunique() if shift_col in df.columns else 0
        cumulative_power = float(df[power_col].sum()) if power_col in df.columns else 0.0

        degradation_factor = (total_shifts * 0.05) + (cumulative_power * 0.001)
        health_score = max(0.0, round(100.0 - degradation_factor, 2))

        return {
            'total_shifts_analyzed': total_shifts,
            'cumulative_power_draw_kwh': round(cumulative_power, 4),
            'computed_health_score': health_score,
        }

    @classmethod
    def run_all(cls, df: pd.DataFrame) -> dict:
        """Runs the full suite of analytics algorithms and returns a consolidated report."""
        return {
            'stress': cls.stress_test_analysis(df),
            'environmental': cls.environmental_analysis(df),
            'vibration': cls.vibration_shock_analysis(df),
            'lifecycle': cls.lifecycle_degradation_analysis(df),
        }
