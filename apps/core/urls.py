"""
Core URL configuration matching Rust backend structure.
"""
from django.urls import path, include
from . import views

urlpatterns = [
    # Health endpoints
    path('health', views.simple_health_check, name='simple_health'),
    
    # Public endpoints
    path('public/', include('apps.projects.urls_public')),
    path('public/', include('apps.contacts.urls')),
    path('public/', include('apps.cv_generator.urls')),
    
    # Auth endpoints
    path('auth/', include('apps.authentication.urls')),
    
    # Protected management endpoints
    path('manage/', include('apps.dashboard.urls')),
    path('manage/', include('apps.projects.urls_manage')),
    path('manage/', include('apps.contacts.urls')),
]