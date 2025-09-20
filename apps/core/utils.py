"""
Core utilities matching Rust backend functionality.
"""
import re
import uuid
import time
import magic
from typing import Dict, Any, Optional
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from rest_framework import status


class ApiResponse:
    """
    API response wrapper matching Rust ApiResponse structure.
    """
    
    @staticmethod
    def success(data: Any = None, message: str = None) -> JsonResponse:
        """Return successful API response."""
        response_data = {
            'success': True,
            'data': data,
            'message': message
        }
        return JsonResponse(response_data, status=status.HTTP_200_OK)
    
    @staticmethod
    def success_with_message(data: Any, message: str) -> JsonResponse:
        """Return successful API response with message."""
        response_data = {
            'success': True,
            'data': data,
            'message': message
        }
        return JsonResponse(response_data, status=status.HTTP_200_OK)
    
    @staticmethod
    def error(message: str, status_code: int = 400, data: Any = None) -> JsonResponse:
        """Return error API response."""
        response_data = {
            'success': False,
            'data': data,
            'message': message
        }
        return JsonResponse(response_data, status=status_code)
    
    @staticmethod
    def validation_error(errors: Dict) -> JsonResponse:
        """Return validation error response."""
        return ApiResponse.error(
            message="Validation errors occurred",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            data={'validation_errors': errors}
        )


class FileValidator:
    """
    File validation utilities matching Rust implementation.
    """
    
    ALLOWED_IMAGE_TYPES = [
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
        'image/webp', 'image/bmp', 'image/tiff'
    ]
    
    ALLOWED_VIDEO_TYPES = [
        'video/mp4', 'video/webm', 'video/ogg', 'video/avi',
        'video/mov', 'video/wmv', 'video/flv', 'video/mkv'
    ]
    
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
    
    @classmethod
    def validate_image(cls, file) -> Dict[str, Any]:
        """Validate uploaded image file."""
        errors = []
        
        # Check file size
        if file.size > cls.MAX_IMAGE_SIZE:
            errors.append(f"Image file too large. Maximum size is {cls.MAX_IMAGE_SIZE // (1024*1024)}MB")
        
        # Check MIME type
        mime_type = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)  # Reset file pointer
        
        if mime_type not in cls.ALLOWED_IMAGE_TYPES:
            errors.append(f"Invalid image type. Allowed types: {', '.join(cls.ALLOWED_IMAGE_TYPES)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'mime_type': mime_type
        }
    
    @classmethod
    def validate_video(cls, file) -> Dict[str, Any]:
        """Validate uploaded video file."""
        errors = []
        
        # Check file size
        if file.size > cls.MAX_VIDEO_SIZE:
            errors.append(f"Video file too large. Maximum size is {cls.MAX_VIDEO_SIZE // (1024*1024)}MB")
        
        # Check MIME type
        mime_type = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)  # Reset file pointer
        
        if mime_type not in cls.ALLOWED_VIDEO_TYPES:
            errors.append(f"Invalid video type. Allowed types: {', '.join(cls.ALLOWED_VIDEO_TYPES)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'mime_type': mime_type
        }


class ValidationUtils:
    """
    Validation utilities matching Rust validation logic.
    """
    
    @staticmethod
    def validate_year(year: str) -> bool:
        """Validate year string (4 digits, reasonable range)."""
        if not re.match(r'^\d{4}$', year):
            return False
        
        year_int = int(year)
        current_year = time.localtime().tm_year
        
        return 2000 <= year_int <= current_year + 1
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength."""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def validate_email_format(email: str) -> bool:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None


class PaginationUtils:
    """
    Pagination utilities matching Rust implementation.
    """
    
    @staticmethod
    def paginate_queryset(queryset, page: int = 1, limit: int = 10):
        """Paginate Django queryset."""
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
        
        try:
            paginator = Paginator(queryset, limit)
            page_obj = paginator.page(page)
            
            return {
                'data': list(page_obj),
                'total': paginator.count,
                'page': page,
                'limit': limit,
                'total_pages': paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            }
        except (EmptyPage, PageNotAnInteger):
            return {
                'data': [],
                'total': 0,
                'page': page,
                'limit': limit,
                'total_pages': 0,
                'has_next': False,
                'has_previous': False
            }
    
    @staticmethod
    def get_pagination_params(request):
        """Extract pagination parameters from request."""
        try:
            page = int(request.GET.get('page', 1))
            limit = int(request.GET.get('limit', 10))
            
            # Ensure reasonable limits
            page = max(1, page)
            limit = min(max(1, limit), 100)  # Max 100 items per page
            
            return page, limit
        except (ValueError, TypeError):
            return 1, 10


def generate_unique_filename(original_name: str) -> str:
    """Generate unique filename while preserving extension."""
    name, ext = original_name.rsplit('.', 1) if '.' in original_name else (original_name, '')
    unique_id = str(uuid.uuid4())
    return f"{unique_id}.{ext}" if ext else unique_id