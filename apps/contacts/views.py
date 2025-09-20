"""
Contact views matching Rust contact handler endpoints.
"""
import logging
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.paginator import Paginator

from .models import Contact
from .serializers import (
    CreateContactRequestSerializer, UpdateContactStatusRequestSerializer,
    ContactResponseSerializer, ContactListResponseSerializer
)
from apps.core.utils import ApiResponse, PaginationUtils

logger = logging.getLogger(__name__)


def get_client_info(request):
    """Extract client information from request."""
    return {
        'ip_address': request.META.get('REMOTE_ADDR'),
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'referrer': request.META.get('HTTP_REFERER', ''),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_contact(request):
    """POST /api/v1/public/contact - Submit contact form"""
    serializer = CreateContactRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return ApiResponse.validation_error(serializer.errors)
    
    client_info = get_client_info(request)
    
    # Create contact with client information
    contact = Contact.objects.create(
        **serializer.validated_data,
        **client_info
    )
    
    logger.info(f"Contact form submitted successfully: {contact.id}")
    
    return ApiResponse.success(
        {"id": str(contact.id)},
        "Thank you for your message! We'll get back to you soon."
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_contacts(request):
    """GET /api/v1/admin/contacts - Get all contacts with pagination"""
    page = int(request.GET.get('page', 1))
    per_page = min(int(request.GET.get('per_page', 20)), 100)
    status_filter = request.GET.get('status')
    search = request.GET.get('search', '').strip()
    
    logger.info(f"Fetching contacts (page: {page}, per_page: {per_page})")
    
    # Build query
    queryset = Contact.objects.all()
    
    if status_filter and status_filter in [choice[0] for choice in Contact.StatusChoices.choices]:
        queryset = queryset.filter(status=status_filter)
    
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(subject__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page)
    
    # Get unread count
    unread_count = Contact.objects.filter(status=Contact.StatusChoices.UNREAD).count()
    
    # Serialize contacts
    contact_serializer = ContactResponseSerializer(page_obj.object_list, many=True)
    
    response_data = {
        'contacts': contact_serializer.data,
        'total': paginator.count,
        'page': page,
        'per_page': per_page,
        'total_pages': paginator.num_pages,
        'unread_count': unread_count,
    }
    
    return ApiResponse.success(response_data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_contact_status(request, contact_id):
    """PUT /api/v1/admin/contacts/{id} - Update contact status"""
    contact = get_object_or_404(Contact, id=contact_id)
    
    serializer = UpdateContactStatusRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return ApiResponse.validation_error(serializer.errors)
    
    # Update contact
    contact.status = serializer.validated_data['status']
    if serializer.validated_data.get('reply_message'):
        contact.reply_message = serializer.validated_data['reply_message']
    
    contact.save()
    
    logger.info(f"Contact {contact_id} status updated successfully")
    
    response_serializer = ContactResponseSerializer(contact)
    return ApiResponse.success(response_serializer.data, "Contact status updated successfully")


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_contact(request, contact_id):
    """DELETE /api/v1/admin/contacts/{id} - Delete contact"""
    contact = get_object_or_404(Contact, id=contact_id)
    contact.delete()
    
    logger.info(f"Contact {contact_id} deleted successfully")
    
    return ApiResponse.success(message="Contact deleted successfully")