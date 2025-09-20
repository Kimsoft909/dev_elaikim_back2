"""
ASGI config for portfolio_backend project.
Configured to use Daphne as the default ASGI server for production deployment.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_backend.settings.development')

application = get_asgi_application()