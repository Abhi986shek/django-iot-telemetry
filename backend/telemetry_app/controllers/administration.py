from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from ..repositories.telemetry_repository import TelemetryRepository
"""
telemetry_app.controllers.administration
-----------------------------------------
HTTP controller for administration and audit endpoints.

All destructive operations require a password that must match the
DELETE_PASSWORD environment variable. Requests with an incorrect
password are rejected with HTTP 403 and logged as warning events.

Endpoints:
    GET  /admin-panel/logs/   -- Renders the ingestion audit log table.
    POST /admin-panel/purge/  -- Deletes all telemetry records for a machine (password-gated).
"""
import logging

logger = logging.getLogger(__name__)
repo = TelemetryRepository()


@login_required
def ingestion_logs(request):
    logs = repo.get_ingestion_logs()
    return render(request, 'admin_logs.html', {'logs': logs})


@login_required
@csrf_exempt
def purge_records(request):
    """
    Password-protected endpoint that deletes all telemetry records for a given machine.
    Requires DELETE_PASSWORD set in the environment.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

    submitted_password = request.POST.get('password', '')
    machine_id = request.POST.get('machine_id', '')

    if not settings.DELETE_PASSWORD or submitted_password != settings.DELETE_PASSWORD:
        logger.warning(f"Unauthorized purge attempt by user: {request.user}")
        return JsonResponse({'error': 'Invalid credentials.'}, status=403)

    deleted_count = repo.purge_machine_records(machine_id)
    logger.info(f"User {request.user} purged {deleted_count} records for machine '{machine_id}'.")
    return JsonResponse({'status': 'success', 'records_deleted': deleted_count})
