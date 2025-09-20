"""
Authentication admin configuration.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, RefreshToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin matching the custom User model."""
    
    list_display = ['email', 'username', 'full_name', 'is_admin', 'is_active', 'failed_login_attempts', 'created_at']
    list_filter = ['is_admin', 'is_active', 'created_at']
    search_fields = ['email', 'username', 'full_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'full_name')}),
        ('Permissions', {'fields': ('is_active', 'is_admin', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Security', {'fields': ('failed_login_attempts', 'locked_until', 'last_login', 'password_changed_at')}),
        ('Important dates', {'fields': ('created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'full_name', 'is_admin'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'password_changed_at']


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    """Refresh token admin."""
    
    list_display = ['user', 'expires_at', 'is_revoked', 'created_at']
    list_filter = ['is_revoked', 'expires_at', 'created_at']
    search_fields = ['user__email', 'user__username']
    ordering = ['-created_at']
    readonly_fields = ['token', 'created_at']