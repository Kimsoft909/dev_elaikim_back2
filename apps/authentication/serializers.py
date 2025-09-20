"""
Authentication serializers matching Rust request/response structures.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User
from apps.core.utils import ValidationUtils


class CreateUserRequestSerializer(serializers.Serializer):
    """Matches Rust CreateUserRequest struct."""
    username = serializers.CharField(min_length=3, max_length=50)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)
    confirm_password = serializers.CharField(min_length=8, max_length=128, write_only=True)
    full_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_email(self, value):
        """Validate email format and uniqueness."""
        if not ValidationUtils.validate_email_format(value):
            raise serializers.ValidationError("Invalid email format")
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists")
        
        return value
    
    def validate_username(self, value):
        """Validate username uniqueness."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("User with this username already exists")
        
        return value
    
    def validate(self, attrs):
        """Validate password match and strength."""
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')
        
        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match")
        
        # Validate password strength
        password_validation = ValidationUtils.validate_password_strength(password)
        if not password_validation['valid']:
            raise serializers.ValidationError(password_validation['errors'])
        
        return attrs


class LoginRequestSerializer(serializers.Serializer):
    """Matches Rust LoginRequest struct."""
    email = serializers.EmailField()
    password = serializers.CharField(min_length=1)
    
    def validate_email(self, value):
        """Validate email format."""
        if not ValidationUtils.validate_email_format(value):
            raise serializers.ValidationError("Invalid email format")
        return value


class ChangePasswordRequestSerializer(serializers.Serializer):
    """Matches Rust ChangePasswordRequest struct."""
    current_password = serializers.CharField(min_length=8, max_length=128)
    new_password = serializers.CharField(min_length=8, max_length=128)
    confirm_password = serializers.CharField(min_length=8, max_length=128)
    
    def validate(self, attrs):
        """Validate password match and strength."""
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        
        if new_password != confirm_password:
            raise serializers.ValidationError("New passwords do not match")
        
        # Validate password strength
        password_validation = ValidationUtils.validate_password_strength(new_password)
        if not password_validation['valid']:
            raise serializers.ValidationError(password_validation['errors'])
        
        return attrs


class RefreshTokenRequestSerializer(serializers.Serializer):
    """Matches Rust RefreshTokenRequest struct.""" 
    refresh_token = serializers.CharField()


class UpdateProfileRequestSerializer(serializers.Serializer):
    """Matches Rust UpdateProfileRequest struct."""
    username = serializers.CharField(min_length=3, max_length=50, required=False)
    email = serializers.EmailField(required=False)
    full_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_email(self, value):
        """Validate email format and uniqueness."""
        if not ValidationUtils.validate_email_format(value):
            raise serializers.ValidationError("Invalid email format")
        
        # Check if email is already taken by another user
        request = self.context.get('request')
        if request and request.user:
            if User.objects.filter(email=value).exclude(id=request.user.id).exists():
                raise serializers.ValidationError("User with this email already exists")
        
        return value
    
    def validate_username(self, value):
        """Validate username uniqueness."""
        request = self.context.get('request')
        if request and request.user:
            if User.objects.filter(username=value).exclude(id=request.user.id).exists():
                raise serializers.ValidationError("User with this username already exists")
        
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """Matches Rust UserProfile struct."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'is_admin', 'created_at']
        read_only_fields = ['id', 'is_admin', 'created_at']


class AuthResponseSerializer(serializers.Serializer):
    """Matches Rust AuthResponse struct."""
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    expires_in = serializers.IntegerField()
    user = UserProfileSerializer()
    
    class Meta:
        fields = ['access_token', 'refresh_token', 'expires_in', 'user']