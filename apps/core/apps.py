"""
Core app configuration with startup hooks.
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    
    def ready(self):
        """
        Called when Django starts up.
        Auto-create superuser from environment variables if needed.
        """
        # Only run in main process to avoid running during migrations
        import os
        # Skip auto-execution during build process
        if os.environ.get('SKIP_AUTO_SUPERUSER'):
            logger.info('Skipping auto-superuser creation (build mode)')
            return
            
        if os.environ.get('RUN_MAIN') or os.environ.get('RENDER'):
            self.ensure_superuser()
    
    def ensure_superuser(self):
        """Auto-create superuser from environment variables."""
        try:
            from django.core.management import call_command
            call_command('ensure_superuser', verbosity=1)
        except Exception as e:
            logger.error(f'Failed to auto-create superuser: {str(e)}', exc_info=True)