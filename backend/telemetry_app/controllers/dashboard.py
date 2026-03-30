"""
telemetry_app.controllers.dashboard
------------------------------------
HTTP controller for dashboard and machine data API endpoints.

This module handles request routing only. All data retrieval is
delegated to TelemetryRepository and all business logic to the
service layer. No ORM queries or data transformations exist here.

Endpoints:
    GET  /           -- Redirect to dashboard if authenticated, else login.
    GET  /dashboard/ -- Render the main analytics dashboard.
    GET  /api/machines/            -- JSON list of all active machine nodes.
    GET  /api/telemetry/<id>/      -- JSON telemetry records for a machine.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ..repositories.telemetry_repository import TelemetryRepository
import logging

logger = logging.getLogger(__name__)
repo = TelemetryRepository()


def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


@login_required
def telemetry_dashboard(request):
    summary = repo.get_dashboard_summary()
    return render(request, 'dashboard.html', {'summary': summary})


@login_required
def machine_list_api(request):
    machines = repo.get_all_machines()
    return JsonResponse({'machines': machines}, safe=False)


@login_required
def telemetry_data_api(request, machine_id):
    limit = int(request.GET.get('limit', 500))
    records = repo.get_telemetry_for_machine(machine_id, limit=limit)
    return JsonResponse({'machine_id': machine_id, 'records': records}, safe=False)
