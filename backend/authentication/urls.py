from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('saml/acs/', views.saml_acs, name='saml_acs'),
    path('saml/metadata/', views.saml_metadata, name='saml_metadata'),
]
