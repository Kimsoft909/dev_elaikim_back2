"""
Dashboard URL patterns for management endpoints.
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('dashboard', views.get_dashboard_stats, name='dashboard_stats'),
    path('health', views.detailed_system_health, name='system_health'),
]