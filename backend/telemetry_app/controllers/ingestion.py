"""
telemetry_app.controllers.ingestion
-------------------------------------
HTTP controller for telemetry file upload and programmatic ingestion.

Handles both browser-based form submissions and raw API requests.
All file processing and database operations are delegated entirely
to ETLService — this module handles only request parsing and response formatting.

Endpoints:
    GET  /upload/      -- Renders the file upload UI.
    POST /upload/      -- Accepts and processes a browser form upload.
    POST /api/ingest/  -- Accepts a programmatic multipart payload (CSRF exempt).
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..services.etl_service import ETLService
import logging

logger = logging.getLogger(__name__)
etl = ETLService()


@login_required
def upload_file(request):
    if request.method == 'GET':
        return render(request, 'upload.html')

    if request.method == 'POST':
        uploaded_file = request.FILES.get('telemetry_file')
        machine_id = request.POST.get('machine_id', '').strip()
        shift_id = request.POST.get('shift_id', '').strip()

        if not uploaded_file or not machine_id:
            return render(request, 'upload.html', {
                'error': 'Machine ID and a telemetry file are required.'
            })

        try:
            result = etl.process_upload(uploaded_file, machine_id, shift_id)
            return render(request, 'upload.html', {'success': result})
        except ValueError as e:
            logger.warning(f"Upload validation failed: {e}")
            return render(request, 'upload.html', {'error': str(e)})
        except Exception as e:
            logger.error(f"Ingestion error for machine {machine_id}: {e}")
            return render(request, 'upload.html', {'error': 'File processing failed. Check format and retry.'})


@csrf_exempt
def api_ingest(request):
    """JSON API endpoint for programmatic telemetry payload submission."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

    uploaded_file = request.FILES.get('telemetry_file')
    machine_id = request.POST.get('machine_id', '').strip()
    shift_id = request.POST.get('shift_id', '').strip()

    if not uploaded_file or not machine_id:
        return JsonResponse({'error': 'machine_id and telemetry_file are required.'}, status=400)

    try:
        result = etl.process_upload(uploaded_file, machine_id, shift_id)
        return JsonResponse({'status': 'success', 'result': result}, status=201)
    except ValueError as e:
        return JsonResponse({'status': 'error', 'detail': str(e)}, status=422)
    except Exception as e:
        logger.error(f"API ingestion error: {e}")
        return JsonResponse({'status': 'error', 'detail': 'Internal processing error.'}, status=500)
