"""
Authentication URL patterns matching Rust auth routes.
"""
from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login', views.login, name='login'),
    path('refresh', views.refresh_token, name='refresh_token'),  
    path('logout', views.logout, name='logout'),
    path('change-password', views.change_password, name='change_password'),
    path('profile', views.get_profile, name='get_profile'),
    path('profile', views.update_profile, name='update_profile'),
]