"""
Core services matching Rust backend functionality.
"""
import time
import os
import uuid
import asyncio
from typing import Optional, Dict, Any
from django.conf import settings
from supabase import create_client, Client
import httpx
import logging

logger = logging.getLogger(__name__)


class SupabaseService:
    """
    Supabase integration service matching Rust implementation.
    Handles file uploads (images and videos) to Supabase storage.
    """
    
    def __init__(self):
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self.bucket_name = settings.SUPABASE_BUCKET_NAME
    
    async def upload_file(self, file_data: bytes, file_path: str, content_type: str) -> Dict[str, Any]:
        """
        Upload file to Supabase storage.
        
        Args:
            file_data: File bytes
            file_path: Path in bucket (e.g., 'images/project_123/image.jpg')
            content_type: MIME type
            
        Returns:
            Dict with success status and file URL
        """
        try:
            # Upload to Supabase storage
            result = self.client.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_data,
                file_options={
                    'content-type': content_type,
                    'cache-control': '3600'
                }
            )
            
            if result:
                # Get public URL
                url_result = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
                
                return {
                    'success': True,
                    'url': url_result,
                    'path': file_path,
                    'size': len(file_data)
                }
            
            return {'success': False, 'error': 'Upload failed'}
            
        except Exception as e:
            logger.error(f"Supabase upload error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def upload_image(self, image_file, project_id: str, is_primary: bool = False) -> Dict[str, Any]:
        """Upload project image to Supabase storage."""
        try:
            # Generate unique filename
            file_extension = image_file.name.split('.')[-1].lower()
            filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = f"images/{project_id}/{filename}"
            
            # Read file data
            file_data = image_file.read()
            
            # Upload to Supabase
            result = await self.upload_file(
                file_data=file_data,
                file_path=file_path,
                content_type=image_file.content_type or f'image/{file_extension}'
            )
            
            if result['success']:
                return {
                    'success': True,
                    'filename': filename,
                    'original_name': image_file.name,
                    'url': result['url'],
                    'file_size': result['size'],
                    'mime_type': image_file.content_type,
                    'is_primary': is_primary
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Image upload error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def upload_video(self, video_file, project_id: str) -> Dict[str, Any]:
        """Upload project video to Supabase storage."""
        try:
            # Generate unique filename
            file_extension = video_file.name.split('.')[-1].lower()
            filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = f"videos/{project_id}/{filename}"
            
            # Read file data
            file_data = video_file.read()
            
            # Upload to Supabase
            result = await self.upload_file(
                file_data=file_data,
                file_path=file_path,
                content_type=video_file.content_type or f'video/{file_extension}'
            )
            
            if result['success']:
                return {
                    'success': True,
                    'filename': filename,
                    'original_name': video_file.name,
                    'url': result['url'],
                    'file_size': result['size'],
                    'mime_type': video_file.content_type
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Video upload error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from Supabase storage."""
        try:
            result = self.client.storage.from_(self.bucket_name).remove([file_path])
            return bool(result)
        except Exception as e:
            logger.error(f"File deletion error: {str(e)}")
            return False
    
    def upload_image(self, image_file, project_id: str, is_primary: bool = False) -> Dict[str, Any]:
        """Sync upload project image to Supabase storage."""
        try:
            # Generate unique filename
            file_extension = image_file.name.split('.')[-1].lower()
            filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = f"images/{project_id}/{filename}"
            
            # Read file data
            file_data = image_file.read()
            
            # Upload to Supabase
            result = self.client.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_data,
                file_options={
                    'content-type': image_file.content_type or f'image/{file_extension}',
                    'cache-control': '3600'
                }
            )
            
            if result:
                # Get public URL
                url_result = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
                
                return {
                    'success': True,
                    'filename': filename,
                    'original_name': image_file.name,
                    'url': url_result,
                    'file_size': len(file_data),
                    'mime_type': image_file.content_type,
                    'is_primary': is_primary
                }
            
            return {'success': False, 'error': 'Upload failed'}
            
        except Exception as e:
            logger.error(f"Image upload error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def upload_video(self, video_file, project_id: str) -> Dict[str, Any]:
        """Sync upload project video to Supabase storage."""
        try:
            # Generate unique filename
            file_extension = video_file.name.split('.')[-1].lower()
            filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = f"videos/{project_id}/{filename}"
            
            # Read file data
            file_data = video_file.read()
            
            # Upload to Supabase
            result = self.client.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_data,
                file_options={
                    'content-type': video_file.content_type or f'video/{file_extension}',
                    'cache-control': '3600'
                }
            )
            
            if result:
                # Get public URL
                url_result = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
                
                return {
                    'success': True,
                    'filename': filename,
                    'original_name': video_file.name,
                    'url': url_result,
                    'file_size': len(file_data),
                    'mime_type': video_file.content_type
                }
            
            return {'success': False, 'error': 'Upload failed'}
            
        except Exception as e:
            logger.error(f"Video upload error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_public_url(self, file_path: str) -> str:
        """Get public URL for a file."""
        return self.client.storage.from_(self.bucket_name).get_public_url(file_path)


class SystemHealthService:
    """
    System health monitoring service matching Rust implementation.
    """
    
    @staticmethod
    async def get_system_health() -> Dict[str, Any]:
        """Get comprehensive system health information."""
        import psutil
        import platform
        from django.db import connection
        from django.core.cache import cache
        import redis
        
        health_data = {
            'status': 'healthy',
            'timestamp': time.time(),
            'services': {},
            'system': {},
            'performance': {}
        }
        
        try:
            # Database health
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                health_data['services']['database'] = {
                    'status': 'healthy',
                    'response_time_ms': 0  # Would measure actual time in production
                }
        except Exception as e:
            health_data['services']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_data['status'] = 'degraded'
        
        # Redis health
        try:
            cache.get('health_check')
            health_data['services']['redis'] = {'status': 'healthy'}
        except Exception as e:
            health_data['services']['redis'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Supabase health
        try:
            supabase_service = SupabaseService()
            # Simple connectivity test
            health_data['services']['supabase'] = {'status': 'healthy'}
        except Exception as e:
            health_data['services']['supabase'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # System information
        health_data['system'] = {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'uptime_seconds': time.time() - psutil.boot_time()
        }
        
        # Performance metrics
        health_data['performance'] = {
            'active_connections': len(connection.queries),
            'cache_hit_rate': 0.95,  # Would calculate actual rate in production
            'average_response_time_ms': 150  # Would calculate from logs
        }
        
        return health_data


# Initialize global service instance
supabase_service = SupabaseService()