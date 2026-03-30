#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    # Add backend/ to path so Django can locate core.settings, telemetry_app, authentication
    backend_dir = Path(__file__).resolve().parent / 'backend'
    sys.path.insert(0, str(backend_dir))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Could not import Django. Ensure it is installed and the virtual environment is active."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
