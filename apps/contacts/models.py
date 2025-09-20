"""
Contact models matching Rust backend Contact struct.
"""
import uuid
from django.db import models
from django.utils import timezone


class Contact(models.Model):
    """
    Contact model matching Rust Contact struct exactly.
    """
    class StatusChoices(models.TextChoices):
        UNREAD = 'unread', 'Unread'
        READ = 'read', 'Read' 
        REPLIED = 'replied', 'Replied'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(
        max_length=20, 
        choices=StatusChoices.choices, 
        default=StatusChoices.UNREAD
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    reply_message = models.TextField(blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contacts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.subject}"
    
    def save(self, *args, **kwargs):
        if self.status == self.StatusChoices.REPLIED and self.reply_message and not self.replied_at:
            self.replied_at = timezone.now()
        super().save(*args, **kwargs)