"""
CV Generator views matching Rust CV handler endpoints (synchronous).
"""
import logging
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from .services import cv_service
from apps.core.utils import ApiResponse

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def download_cv(request):
    """GET /api/v1/public/cv/download - Download CV as PDF or HTML"""
    format_type = request.GET.get('format', 'pdf').lower()
    theme = request.GET.get('theme', 'professional')

    logger.info(f"CV download request - format: {format_type}, theme: {theme}")

    try:
        if format_type == 'pdf':
            # Use request.build_absolute_uri('/') as base_url for static resolution
            pdf_data = cv_service.generate_pdf(
                theme=theme,
                base_url=request.build_absolute_uri('/')
            )

            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename=\"CV_Resume.pdf\"'
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

            logger.info(f"CV PDF generated successfully, size: {len(pdf_data)} bytes")
            return response

        elif format_type == 'html':
            html_content = cv_service.generate_html_cv(theme=theme)

            response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
            response['Content-Disposition'] = 'attachment; filename=\"CV_Resume.html\"'

            logger.info(f"CV HTML generated successfully, size: {len(html_content)} bytes")
            return response

        else:
            return ApiResponse.error("Invalid format. Supported formats: pdf, html")

    except Exception as e:
        logger.error(f"CV generation error: {e}", exc_info=True)
        return ApiResponse.error("Failed to generate CV. Please try again later.")


@api_view(['GET'])
@permission_classes([AllowAny])
def preview_cv(request):
    """GET /api/v1/public/cv/preview - Preview CV as HTML"""
    theme = request.GET.get('theme', 'professional')

    logger.info(f"CV preview request - theme: {theme}")

    try:
        html_content = cv_service.generate_html_cv(theme=theme)

        response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
        response['Cache-Control'] = 'public, max-age=300'  # Cache for 5 minutes

        logger.info("CV preview HTML generated successfully")
        return response

    except Exception as e:
        logger.error(f"CV preview generation error: {e}", exc_info=True)
        return ApiResponse.error("Failed to generate CV preview. Please try again later.")
