"""
Admin project URLs (authentication required).
"""
from django.urls import path
from . import views

app_name = 'projects_manage'

urlpatterns = [
    path('projects', views.create_project, name='project_create'),
    path('projects/<uuid:project_id>', views.update_project, name='project_update'),
    path('projects/<uuid:project_id>/delete', views.delete_project, name='project_delete'),
]