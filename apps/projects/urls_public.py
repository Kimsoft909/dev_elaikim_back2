"""
Public project URLs (no authentication required).
"""
from django.urls import path
from . import views

app_name = 'projects_public'

urlpatterns = [
    path('projects', views.get_all_projects, name='project_list'),
    path('projects/<uuid:project_id>', views.get_project, name='project_detail'),
]