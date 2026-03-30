"""
authentication.views
---------------------
Handles all authentication flows for the platform.

Supports two authentication methods:

    1. Local Authentication
       Standard Django username/password login backed by the built-in
       User model. Suitable for development and small deployments.

    2. SAML 2.0 Single Sign-On (SSO)
       Enterprise-grade authentication via an external Identity Provider (IdP)
       such as Azure AD, Okta, or any SAML-compliant system. Requires the
       python3-saml library and a configured saml/settings.json file.

Endpoints:
    GET/POST /auth/login/          -- Login page with local and SSO options.
    POST     /auth/logout/         -- Terminates the user session.
    POST     /auth/saml/acs/       -- SAML Assertion Consumer Service endpoint.
    GET      /auth/saml/metadata/  -- Returns SAML SP metadata XML for IdP registration.
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.conf import settings

try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.settings import OneLogin_Saml2_Settings
    SAML_AVAILABLE = True
except ImportError:
    SAML_AVAILABLE = False

logger = logging.getLogger(__name__)


def _prepare_saml_request(request):
    return {
        'https': 'on' if request.is_secure() else 'off',
        'http_host': request.META['HTTP_HOST'],
        'script_name': request.META['PATH_INFO'],
        'get_data': request.GET.copy(),
        'post_data': request.POST.copy(),
    }


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        return render(request, 'login.html', {'error': 'Invalid credentials.'})

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def saml_acs(request):
    """
    SAML 2.0 Assertion Consumer Service.
    Validates the IdP response and creates or updates the local user session.
    """
    if not SAML_AVAILABLE:
        return HttpResponse('SAML library not installed.', status=501)

    req = _prepare_saml_request(request)
    auth = OneLogin_Saml2_Auth(req, custom_base_path=str(settings.SAML_FOLDER))
    auth.process_response()

    errors = auth.get_errors()
    if errors:
        logger.error(f"SAML ACS error: {errors}")
        return render(request, 'login.html', {'error': 'SSO authentication failed.'})

    if not auth.is_authenticated():
        return render(request, 'login.html', {'error': 'SSO session could not be established.'})

    saml_attributes = auth.get_attributes()
    name_id = auth.get_nameid()

    user, created = User.objects.get_or_create(
        username=name_id,
        defaults={
            'email': name_id,
            'first_name': saml_attributes.get('firstName', [''])[0],
            'last_name': saml_attributes.get('lastName', [''])[0],
        }
    )

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('dashboard')


def saml_metadata(request):
    """Returns the SAML SP metadata XML for IdP configuration."""
    if not SAML_AVAILABLE:
        return HttpResponse('SAML library not installed.', status=501)

    saml_settings = OneLogin_Saml2_Settings(
        custom_base_path=str(settings.SAML_FOLDER),
        sp_validation_only=True
    )
    metadata = saml_settings.get_sp_metadata()
    errors = saml_settings.validate_metadata(metadata)

    if errors:
        return HttpResponse(', '.join(errors), content_type='text/plain', status=500)

    return HttpResponse(metadata, content_type='text/xml')
