"""
Project URL patterns matching Rust routes.
"""
from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # Public endpoints
    path('projects/', views.get_all_projects, name='get_all_projects'),
    path('projects/<uuid:project_id>/', views.get_project, name='get_project'),
    
    # Admin endpoints  
    path('projects', views.create_project, name='create_project'),
    path('projects/<uuid:project_id>/', views.update_project, name='update_project'),
    path('projects/<uuid:project_id>/', views.delete_project, name='delete_project'),
]