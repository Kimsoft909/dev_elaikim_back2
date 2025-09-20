"""
Advanced Project admin configuration with file upload handling.
"""
from django import forms
from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Project, ProjectImage
from apps.core.services import supabase_service
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ProjectImageInline(admin.TabularInline):
    """Inline for project images."""
    model = ProjectImage
    extra = 0
    readonly_fields = ('url', 'file_size', 'mime_type', 'created_at')
    fields = ('original_name', 'url', 'is_primary', 'sort_order', 'file_size', 'mime_type', 'created_at')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields
        else:  # Adding new object
            return ('file_size', 'mime_type', 'created_at')


class MultiFileInput(forms.ClearableFileInput):
    """Custom ClearableFileInput that supports multiple files."""
    allow_multiple_selected = True


class ProjectAdminForm(forms.ModelForm):
    """Custom form for Project admin with file upload widgets."""
    
    images = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={'multiple': True}),
        help_text="Upload project images (multiple files allowed). Images will be uploaded to Supabase."
    )
    
    demo_video = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(),
        help_text="Upload demo video. Video will be uploaded to Supabase."
    )
    
    class Meta:
        model = Project
        fields = '__all__'
        widgets = {
            'technologies': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Enter technologies as JSON array, e.g., [\"React\", \"Django\", \"PostgreSQL\"]'
            }),
            'features': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Enter features as JSON array, e.g., [\"User Authentication\", \"Real-time Updates\"]'
            }),
            'long_description': forms.Textarea(attrs={'rows': 5}),
        }


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Advanced Project admin with bulk operations and file handling."""
    
    form = ProjectAdminForm
    inlines = [ProjectImageInline]
    
    list_display = [
        'title', 'year', 'is_featured', 'image_count', 'has_video', 
        'tech_count', 'sort_order', 'created_at'
    ]
    
    list_filter = [
        'is_featured', 'year', 'created_at', 'updated_at'
    ]
    
    search_fields = [
        'title', 'description', 'long_description', 'technologies', 'features'
    ]
    
    readonly_fields = ['id', 'created_at', 'updated_at', 'image_preview']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'long_description')
        }),
        ('Technical Details', {
            'fields': ('technologies', 'features', 'duration', 'team_size', 'year')
        }),
        ('URLs', {
            'fields': ('github_url', 'live_url', 'demo_video_url'),
            'description': 'Add project URLs here.'
        }),
        ('Media Upload', {
            'fields': ('images', 'demo_video'),
            'description': 'Upload new files here. They will be uploaded to Supabase automatically.'
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'sort_order')
        }),
        ('System Fields', {
            'fields': ('id', 'created_at', 'updated_at', 'image_preview'),
            'classes': ('collapse',)
        })
    )
    
    ordering = ['sort_order', '-created_at']
    list_per_page = 25
    
    # Bulk actions
    actions = [
        'make_featured', 'remove_featured', 'duplicate_projects', 
        'export_projects_csv', 'bulk_update_year'
    ]
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('images')
    
    def image_count(self, obj):
        count = obj.images.count()
        if count > 0:
            url = reverse('admin:projects_projectimage_changelist')
            return format_html(
                '<a href="{}?project__id__exact={}">{} images</a>',
                url, obj.id, count
            )
        return "No images"
    image_count.short_description = "Images"
    
    def has_video(self, obj):
        return bool(obj.demo_video_url)
    has_video.boolean = True
    has_video.short_description = "Video"
    
    def tech_count(self, obj):
        if obj.technologies:
            return len(obj.technologies)
        return 0
    tech_count.short_description = "Tech Count"
    
    def image_preview(self, obj):
        primary_image = obj.primary_image
        if primary_image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 150px;" />',
                primary_image.url
            )
        return "No primary image"
    image_preview.short_description = "Primary Image Preview"
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        if 'images' in request.FILES:
            self._handle_image_uploads(obj, request.FILES.getlist('images'))
        
        if 'demo_video' in request.FILES:
            self._handle_video_upload(obj, request.FILES['demo_video'])
    
    def _handle_image_uploads(self, project, image_files):
        for image_file in image_files:
            try:
                file_url = supabase_service.upload_file(
                    image_file,
                    bucket_name=settings.SUPABASE_BUCKET_NAME,
                    folder=f"projects/{project.id}/images"
                )
                
                ProjectImage.objects.create(
                    project=project,
                    filename=f"{project.id}_{image_file.name}",
                    original_name=image_file.name,
                    url=file_url,
                    file_size=image_file.size,
                    mime_type=image_file.content_type,
                    is_primary=not project.images.exists()
                )
                
                logger.info(f"Image uploaded successfully: {image_file.name}")
            except Exception as e:
                logger.error(f"Failed to upload image {image_file.name}: {e}")
    
    def _handle_video_upload(self, project, video_file):
        try:
            video_url = supabase_service.upload_file(
                video_file,
                bucket_name=settings.SUPABASE_BUCKET_NAME,
                folder=f"projects/{project.id}/videos"
            )
            
            project.demo_video_url = video_url
            project.save(update_fields=['demo_video_url'])
            
            logger.info(f"Video uploaded successfully: {video_file.name}")
        except Exception as e:
            logger.error(f"Failed to upload video {video_file.name}: {e}")
    
    # Bulk Actions
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} projects marked as featured.")
    make_featured.short_description = "Mark selected projects as featured"
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f"Featured status removed from {updated} projects.")
    remove_featured.short_description = "Remove featured status"
    
    def duplicate_projects(self, request, queryset):
        duplicated = 0
        for project in queryset:
            project.pk = None
            project.title = f"{project.title} (Copy)"
            project.is_featured = False
            project.save()
            duplicated += 1
        self.message_user(request, f"{duplicated} projects duplicated successfully.")
    duplicate_projects.short_description = "Duplicate selected projects"
    
    def export_projects_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="projects_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Title', 'Description', 'Year', 'Technologies', 'Features',
            'GitHub URL', 'Live URL', 'Is Featured', 'Created At'
        ])
        
        for project in queryset:
            writer.writerow([
                project.title,
                project.description,
                project.year,
                ', '.join(project.technologies) if project.technologies else '',
                ', '.join(project.features) if project.features else '',
                project.github_url,
                project.live_url,
                project.is_featured,
                project.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_projects_csv.short_description = "Export selected projects to CSV"
    
    def bulk_update_year(self, request, queryset):
        from datetime import datetime
        current_year = str(datetime.now().year)
        updated = queryset.update(year=current_year)
        self.message_user(request, f"Year updated to {current_year} for {updated} projects.")
    bulk_update_year.short_description = f"Update year to current year"


@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    """Project Image admin."""
    
    list_display = [
        'project', 'original_name', 'is_primary', 'file_size_mb', 
        'mime_type', 'sort_order', 'created_at'
    ]
    
    list_filter = ['is_primary', 'mime_type', 'created_at']
    
    search_fields = ['project__title', 'original_name', 'filename']
    
    readonly_fields = ['id', 'url', 'file_size', 'mime_type', 'created_at', 'image_preview']
    
    fieldsets = (
        ('Image Information', {
            'fields': ('project', 'original_name', 'filename', 'url')
        }),
        ('Settings', {
            'fields': ('is_primary', 'sort_order')
        }),
        ('File Details', {
            'fields': ('file_size', 'mime_type', 'created_at'),
            'classes': ('collapse',)
        }),
        ('Preview', {
            'fields': ('image_preview',)
        })
    )
    
    ordering = ['project', 'sort_order', 'created_at']
    list_per_page = 50
    
    def file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return "Unknown"
    file_size_mb.short_description = "File Size"
    
    def image_preview(self, obj):
        if obj.url:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 200px;" />',
                obj.url
            )
        return "No image"
    image_preview.short_description = "Image Preview"
