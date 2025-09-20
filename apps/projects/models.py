"""
Project models matching Rust backend Project and ProjectImage structs.
"""
import uuid
from django.db import models
from django.core.validators import RegexValidator
from apps.authentication.models import User


class Project(models.Model):
    """
    Project model matching Rust Project struct exactly.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=500)
    long_description = models.TextField(blank=True)
    technologies = models.JSONField(default=list)  # JSON array
    features = models.JSONField(default=list)  # JSON array
    github_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    duration = models.CharField(max_length=100, blank=True)
    team_size = models.CharField(max_length=100, blank=True)
    year = models.CharField(
        max_length=4,
        validators=[RegexValidator(regex=r'^\d{4}$', message='Year must be 4 digits')]
    )
    demo_video_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'projects'
        ordering = ['sort_order', '-created_at']
        indexes = [
            models.Index(fields=['is_featured']),
            models.Index(fields=['sort_order']),
            models.Index(fields=['year']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def primary_image(self):
        """Get the primary image for this project."""
        return self.images.filter(is_primary=True).first()
    
    @property
    def all_images(self):
        """Get all images ordered by sort_order."""
        return self.images.all().order_by('sort_order', 'created_at')


class ProjectImage(models.Model):
    """
    Project image model matching Rust ProjectImage struct exactly.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, related_name='images', on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    original_name = models.CharField(max_length=255)
    url = models.URLField()
    file_size = models.BigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_images'
        ordering = ['sort_order', 'created_at']
        indexes = [
            models.Index(fields=['project', 'is_primary']),
            models.Index(fields=['project', 'sort_order']),
        ]
    
    def __str__(self):
        return f"{self.project.title} - {self.original_name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary image per project
        if self.is_primary:
            ProjectImage.objects.filter(
                project=self.project,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        
        super().save(*args, **kwargs)