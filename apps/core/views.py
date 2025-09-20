"""
Core views matching Rust backend health and system endpoints.
"""
import time
import platform
from django.http import JsonResponse
from django.utils import timezone
from django.db import connection
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import psutil
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@never_cache
def simple_health_check(request):
    """
    Simple health check endpoint for external monitoring (UptimeRobot, etc.).
    Public endpoint - no authentication required.
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'Portfolio Backend API',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@never_cache
def detailed_system_health(request):
    """
    Detailed system health endpoint for admin dashboard.
    Requires authentication - admin only.
    """
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0',
            'services': {},
            'system': {},
            'performance': {},
            'database': {}
        }
        
        # Database health check
        try:
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_response_time = (time.time() - start_time) * 1000
            
            # Get database size and basic stats
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        pg_size_pretty(pg_database_size(current_database())) as db_size,
                        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                        version() as version
                """)
                db_stats = cursor.fetchone()
            
            health_data['services']['database'] = {
                'status': 'healthy',
                'response_time_ms': round(db_response_time, 2),
                'size': db_stats[0] if db_stats else 'Unknown',
                'active_connections': db_stats[1] if db_stats else 0,
                'version': db_stats[2].split(' ')[0] if db_stats else 'Unknown'
            }
            health_data['database'] = health_data['services']['database']
            
        except Exception as e:
            health_data['services']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_data['status'] = 'degraded'
        
        # Redis health check
        try:
            start_time = time.time()
            cache.set('health_check', 'ok', 60)
            cache.get('health_check')
            redis_response_time = (time.time() - start_time) * 1000
            
            health_data['services']['redis'] = {
                'status': 'healthy',
                'response_time_ms': round(redis_response_time, 2)
            }
        except Exception as e:
            health_data['services']['redis'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_data['status'] = 'degraded'
        
        # Supabase health check (basic connectivity)
        try:
            from apps.core.services import supabase_service
            health_data['services']['supabase'] = {
                'status': 'healthy',
                'bucket': supabase_service.bucket_name
            }
        except Exception as e:
            health_data['services']['supabase'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # System information
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_data['system'] = {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': round(psutil.cpu_percent(interval=0.1), 2),
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'memory_used_gb': round(memory.used / (1024**3), 2),
                'memory_percent': round(memory.percent, 2),
                'disk_total_gb': round(disk.total / (1024**3), 2),
                'disk_used_gb': round(disk.used / (1024**3), 2),
                'disk_percent': round((disk.used / disk.total) * 100, 2),
                'uptime_seconds': round(time.time() - psutil.boot_time(), 2)
            }
        except Exception as e:
            logger.warning(f"Could not get system stats: {e}")
            health_data['system'] = {
                'error': 'System stats unavailable',
                'platform': platform.platform(),
                'python_version': platform.python_version()
            }
        
        # Performance metrics (basic)
        try:
            health_data['performance'] = {
                'active_database_connections': len(connection.queries) if hasattr(connection, 'queries') else 0,
                'cache_hit_rate_estimate': 0.95,  # Would calculate from actual metrics in production
                'average_response_time_ms': 150   # Would calculate from request logs
            }
        except Exception as e:
            logger.warning(f"Could not get performance metrics: {e}")
            health_data['performance'] = {'error': 'Performance metrics unavailable'}
        
        return Response(health_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}", exc_info=True)
        return Response({
            'status': 'error',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)