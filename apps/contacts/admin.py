"""
Contact admin interface with enhanced bulk actions and management features.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponse
import csv
from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'status_display', 'country', 'created_at_display']
    list_filter = ['status', 'created_at', 'country', 'replied_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['id', 'created_at', 'updated_at', 'ip_address', 'user_agent']
    list_per_page = 50
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_replied', 'mark_as_unread', 'export_to_csv', 'bulk_reply']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'subject', 'message')
        }),
        ('Status Management', {
            'fields': ('status', 'reply_message', 'replied_at')
        }),
        ('Analytics & Metadata', {
            'fields': ('ip_address', 'user_agent', 'referrer', 'country'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        """Display status with colored badge."""
        colors = {
            'unread': 'red',
            'read': 'orange', 
            'replied': 'green'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def created_at_display(self, obj):
        """Display formatted creation date."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.short_description = 'Created'
    created_at_display.admin_order_field = 'created_at'
    
    def get_queryset(self, request):
        """Optimize queryset with annotations."""
        return super().get_queryset(request).select_related()
    
    # Bulk Actions
    def mark_as_read(self, request, queryset):
        """Mark selected contacts as read."""
        updated = queryset.filter(status='unread').update(status='read')
        self.message_user(request, f'{updated} contacts marked as read.', messages.SUCCESS)
    mark_as_read.short_description = 'Mark selected as read'
    
    def mark_as_replied(self, request, queryset):
        """Mark selected contacts as replied."""
        updated = queryset.exclude(status='replied').update(
            status='replied',
            replied_at=timezone.now()
        )
        self.message_user(request, f'{updated} contacts marked as replied.', messages.SUCCESS)
    mark_as_replied.short_description = 'Mark selected as replied'
    
    def mark_as_unread(self, request, queryset):
        """Mark selected contacts as unread."""
        updated = queryset.exclude(status='unread').update(status='unread')
        self.message_user(request, f'{updated} contacts marked as unread.', messages.SUCCESS)
    mark_as_unread.short_description = 'Mark selected as unread'
    
    def export_to_csv(self, request, queryset):
        """Export selected contacts to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="contacts_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Name', 'Email', 'Subject', 'Message', 'Status', 
            'Country', 'IP Address', 'Created At', 'Replied At'
        ])
        
        for contact in queryset:
            writer.writerow([
                contact.name,
                contact.email,
                contact.subject,
                contact.message,
                contact.get_status_display(),
                contact.country or '',
                contact.ip_address or '',
                contact.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                contact.replied_at.strftime('%Y-%m-%d %H:%M:%S') if contact.replied_at else ''
            ])
        
        self.message_user(request, f'{queryset.count()} contacts exported to CSV.', messages.SUCCESS)
        return response
    export_to_csv.short_description = 'Export selected to CSV'
    
    def changelist_view(self, request, extra_context=None):
        """Add summary statistics to the changelist view."""
        extra_context = extra_context or {}
        
        # Get contact statistics
        total_contacts = Contact.objects.count()
        unread_contacts = Contact.objects.filter(status='unread').count()
        replied_contacts = Contact.objects.filter(status='replied').count()
        
        extra_context['contact_stats'] = {
            'total': total_contacts,
            'unread': unread_contacts,
            'replied': replied_contacts,
            'read': total_contacts - unread_contacts - replied_contacts
        }
        
        return super().changelist_view(request, extra_context)