"""
Rate limiting middleware matching Rust implementation.
"""
import redis
import json
import time
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware that matches the Rust backend implementation.
    - 60 requests per minute
    - Burst of 10 requests
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
        self.requests_per_minute = getattr(settings, 'RATE_LIMIT_REQUESTS_PER_MINUTE', 60)
        self.burst_limit = getattr(settings, 'RATE_LIMIT_BURST', 10)
        super().__init__(get_response)
    
    def process_request(self, request):
        # Skip rate limiting for admin and static files
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return None
            
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Rate limit key
        rate_limit_key = f"rate_limit:{client_ip}"
        burst_key = f"burst_limit:{client_ip}"
        
        try:
            # Check burst limit first
            burst_count = cache.get(burst_key, 0)
            if burst_count >= self.burst_limit:
                return self.rate_limit_response()
            
            # Check per-minute limit
            current_minute = int(time.time() // 60)
            minute_key = f"{rate_limit_key}:{current_minute}"
            
            request_count = cache.get(minute_key, 0)
            if request_count >= self.requests_per_minute:
                return self.rate_limit_response()
            
            # Increment counters
            cache.set(burst_key, burst_count + 1, timeout=10)  # 10 second burst window
            cache.set(minute_key, request_count + 1, timeout=60)  # 1 minute window
            
        except Exception as e:
            # If Redis fails, allow the request through
            pass
        
        return None
    
    def get_client_ip(self, request):
        """Extract client IP from request headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def rate_limit_response(self):
        """Return rate limit exceeded response."""
        return JsonResponse({
            'success': False,
            'message': 'Rate limit exceeded. Please try again later.',
            'data': None
        }, status=429)


class RequestLoggingMiddleware(MiddlewareMixin):
    """Log requests for monitoring and debugging."""
    
    def process_request(self, request):
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log slow requests (>1 second)
            if duration > 1.0:
                import logging
                logger = logging.getLogger('portfolio_backend')
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s - Status: {response.status_code}"
                )
        
        return response