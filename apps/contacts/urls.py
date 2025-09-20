"""
Contact URL patterns matching Rust handler endpoints.
"""
from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    # Public endpoint
    path('contact', views.submit_contact, name='submit_contact'),
    
    # Management endpoints (will be accessed via /manage/ prefix)
    path('contacts', views.get_all_contacts, name='get_all_contacts'),
    path('contacts/<uuid:contact_id>', views.update_contact_status, name='update_contact_status'),
    path('contacts/<uuid:contact_id>/delete', views.delete_contact, name='delete_contact'),
]