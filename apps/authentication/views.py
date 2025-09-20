"""
Authentication views matching Rust handler endpoints.
"""
import logging
from datetime import timedelta
from django.contrib.auth import authenticate
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import User, RefreshToken as CustomRefreshToken
from .serializers import (
    LoginRequestSerializer, ChangePasswordRequestSerializer,
    RefreshTokenRequestSerializer, UpdateProfileRequestSerializer,
    UserProfileSerializer, AuthResponseSerializer
)
from apps.core.utils import ApiResponse

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login endpoint matching Rust handler.
    POST /api/v1/auth/login
    """
    serializer = LoginRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return ApiResponse.validation_error(serializer.errors)
    
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    
    try:
        user = User.objects.get(email=email)
        
        # Check if account is locked
        if user.is_account_locked:
            return ApiResponse.error(
                "Account is temporarily locked due to multiple failed login attempts. Please try again later.",
                status_code=status.HTTP_423_LOCKED
            )
        
        # Check if account is active
        if not user.is_active:
            return ApiResponse.error(
                "Account is deactivated. Please contact administrator.",
                status_code=status.HTTP_403_FORBIDDEN  
            )
        
        # Authenticate user
        authenticated_user = authenticate(request, username=email, password=password)
        
        if authenticated_user:
            # Reset failed attempts on successful login
            user.reset_failed_attempts()
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            # Store refresh token in database
            CustomRefreshToken.objects.create(
                user=user,
                token=refresh_token,
                expires_at=timezone.now() + timedelta(days=7)
            )
            
            # Prepare response data
            user_profile = UserProfileSerializer(user).data
            
            response_data = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': 3600,  # 1 hour in seconds
                'user': user_profile
            }
            
            logger.info(f"User {email} logged in successfully")
            # Return direct response format expected by frontend
            from django.http import JsonResponse
            return JsonResponse(response_data, status=200)
        
        else:
            # Increment failed attempts
            user.increment_failed_attempts()
            
            return ApiResponse.error(
                "Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
    
    except User.DoesNotExist:
        return ApiResponse.error(
            "Invalid email or password",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return ApiResponse.error(
            "An error occurred during login. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh token endpoint matching Rust handler.
    POST /api/v1/auth/refresh
    """
    serializer = RefreshTokenRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return ApiResponse.validation_error(serializer.errors)
    
    refresh_token_str = serializer.validated_data['refresh_token']
    
    try:
        # Validate refresh token in database
        custom_token = CustomRefreshToken.objects.get(
            token=refresh_token_str,
            is_revoked=False
        )
        
        if custom_token.is_expired:
            custom_token.revoke()
            return ApiResponse.error(
                "Refresh token has expired",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate new tokens
        refresh = RefreshToken(refresh_token_str)
        new_access_token = str(refresh.access_token)
        
        # Optionally rotate refresh token
        new_refresh = RefreshToken.for_user(custom_token.user)
        new_refresh_token = str(new_refresh)
        
        # Revoke old token and create new one
        custom_token.revoke()
        CustomRefreshToken.objects.create(
            user=custom_token.user,
            token=new_refresh_token,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        response_data = {
            'access_token': new_access_token,
            'refresh_token': new_refresh_token,
            'expires_in': 3600,  # 1 hour in seconds
            'user': UserProfileSerializer(custom_token.user).data
        }
        
        # Return direct response format expected by frontend
        from django.http import JsonResponse
        return JsonResponse(response_data, status=200)
    
    except CustomRefreshToken.DoesNotExist:
        return ApiResponse.error(
            "Invalid refresh token",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    except TokenError:
        return ApiResponse.error(
            "Invalid refresh token",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return ApiResponse.error(
            "An error occurred while refreshing token. Please login again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout endpoint matching Rust handler.
    POST /api/v1/auth/logout
    """
    try:
        # Get refresh token from request data or headers
        refresh_token_str = request.data.get('refresh_token')
        
        if refresh_token_str:
            # Revoke specific refresh token
            CustomRefreshToken.objects.filter(
                user=request.user,
                token=refresh_token_str
            ).update(is_revoked=True)
        else:
            # Revoke all user's refresh tokens
            CustomRefreshToken.objects.filter(
                user=request.user,
                is_revoked=False
            ).update(is_revoked=True)
        
        logger.info(f"User {request.user.email} logged out successfully")
        return ApiResponse.success(message="Logged out successfully")
    
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return ApiResponse.error(
            "An error occurred during logout",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change password endpoint matching Rust handler.
    POST /api/v1/auth/change-password
    """
    serializer = ChangePasswordRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return ApiResponse.validation_error(serializer.errors)
    
    current_password = serializer.validated_data['current_password']
    new_password = serializer.validated_data['new_password']
    
    user = request.user
    
    # Verify current password
    if not check_password(current_password, user.password):
        return ApiResponse.error(
            "Current password is incorrect",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Change password
    user.set_password(new_password)
    user.password_changed_at = timezone.now()
    user.save()
    
    # Revoke all refresh tokens to force re-login on other devices
    CustomRefreshToken.objects.filter(
        user=user,
        is_revoked=False
    ).update(is_revoked=True)
    
    logger.info(f"Password changed for user {user.email}")
    return ApiResponse.success(message="Password changed successfully")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """
    Get user profile endpoint matching Rust handler.
    GET /api/v1/auth/profile
    """
    serializer = UserProfileSerializer(request.user)
    return ApiResponse.success(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update user profile endpoint matching Rust handler.
    PUT /api/v1/auth/profile
    """
    serializer = UpdateProfileRequestSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if not serializer.is_valid():
        return ApiResponse.validation_error(serializer.errors)
    
    user = request.user
    
    # Update user fields
    for field, value in serializer.validated_data.items():
        setattr(user, field, value)
    
    user.updated_at = timezone.now()
    user.save()
    
    # Return updated profile
    updated_profile = UserProfileSerializer(user).data
    
    logger.info(f"Profile updated for user {user.email}")
    return ApiResponse.success(updated_profile, "Profile updated successfully")