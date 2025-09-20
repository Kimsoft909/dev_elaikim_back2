"""
Dashboard views matching Rust admin handler endpoints.
"""
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .services import health_service, dashboard_service
from apps.core.utils import ApiResponse

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_stats(request):
    """GET /api/v1/admin/dashboard - Get dashboard statistics"""
    try:
        stats = dashboard_service.get_dashboard_stats()
        logger.info("Dashboard stats fetched successfully")
        return ApiResponse.success(stats)
        
    except Exception as e:
        logger.error(f"Failed to fetch dashboard stats: {e}")
        return ApiResponse.error("Failed to fetch dashboard statistics")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detailed_system_health(request):
    """GET /api/v1/manage/system-health - Get detailed system health for admin"""
    try:
        from apps.core.services import SystemHealthService
        import asyncio
        
        # Get system health data
        health_data = asyncio.run(SystemHealthService.get_system_health())
        
        logger.info("System health data fetched successfully")
        return ApiResponse.success(health_data)
        
    except Exception as e:
        logger.error(f"Failed to fetch system health: {e}")
        return ApiResponse.error("Failed to fetch system health data")