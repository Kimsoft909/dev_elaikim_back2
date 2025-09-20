"""
Dashboard services for health monitoring and stats.
"""
import logging
import psutil
import redis
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from apps.projects.models import Project
from apps.contacts.models import Contact

logger = logging.getLogger(__name__)


class HealthService:
    """
    Health monitoring service matching Rust implementation.
    """
    
    def __init__(self):
        self.redis_client = None
        try:
            self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
    
    def get_system_health(self):
        """Get comprehensive system health status."""
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'services': {},
            'metrics': {}
        }
        
        # Database health
        health_data['services']['database'] = self._check_database()
        
        # Redis health
        health_data['services']['redis'] = self._check_redis()
        
        # System metrics
        health_data['metrics'] = self._get_system_metrics()
        
        # Overall status
        if any(service['status'] != 'healthy' for service in health_data['services'].values()):
            health_data['status'] = 'degraded'
        
        return health_data
    
    def _check_database(self):
        """Check database connectivity."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
            return {
                'status': 'healthy',
                'response_time_ms': 0,  # Would need timing logic
                'connection_count': self._get_db_connections()
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _check_redis(self):
        """Check Redis connectivity."""
        if not self.redis_client:
            return {
                'status': 'unavailable',
                'error': 'Redis client not initialized'
            }
        
        try:
            start_time = timezone.now()
            self.redis_client.ping()
            response_time = (timezone.now() - start_time).total_seconds() * 1000
            
            info = self.redis_client.info()
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'memory_usage_mb': round(info.get('used_memory', 0) / 1024 / 1024, 2),
                'connected_clients': info.get('connected_clients', 0)
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _get_system_metrics(self):
        """Get system performance metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_usage_percent': round(cpu_percent, 2),
                'memory_usage_percent': round(memory.percent, 2),
                'memory_available_mb': round(memory.available / 1024 / 1024, 2),
                'disk_usage_percent': round(disk.percent, 2),
                'disk_free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
                'load_average': list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [],
            }
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
            return {}
    
    def _get_db_connections(self):
        """Get database connection count."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
                return cursor.fetchone()[0]
        except Exception:
            return 0


class DashboardService:
    """
    Dashboard statistics service.
    """
    
    def get_dashboard_stats(self):
        """Get dashboard statistics matching Rust DashboardStats."""
        cache_key = 'dashboard_stats'
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            return cached_stats
        
        # Calculate stats
        stats = {
            'total_projects': Project.objects.count(),
            'featured_projects': Project.objects.filter(is_featured=True).count(),
            'total_contacts': Contact.objects.count(),
            'unread_contacts': Contact.objects.filter(status=Contact.StatusChoices.UNREAD).count(),
            'read_contacts': Contact.objects.filter(status=Contact.StatusChoices.READ).count(),
            'replied_contacts': Contact.objects.filter(status=Contact.StatusChoices.REPLIED).count(),
            'recent_contacts': self._get_recent_contacts(),
        }
        
        # Cache for 1 minute
        cache.set(cache_key, stats, 60)
        
        return stats
    
    def _get_recent_contacts(self, limit=5):
        """Get recent contacts for dashboard."""
        recent_contacts = Contact.objects.select_related().order_by('-created_at')[:limit]
        
        return [
            {
                'id': str(contact.id),
                'name': contact.name,
                'email': contact.email,
                'subject': contact.subject,
                'status': contact.status,
                'created_at': contact.created_at.isoformat(),
            }
            for contact in recent_contacts
        ]


# Global service instances
health_service = HealthService()
dashboard_service = DashboardService()