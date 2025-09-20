"""
CV Generator URL patterns matching Rust handler endpoints.
"""
from django.urls import path
from . import views

app_name = 'cv_generator'

urlpatterns = [
    path('cv/download/', views.download_cv, name='download_cv'),
    path('cv/preview/', views.preview_cv, name='preview_cv'),
]