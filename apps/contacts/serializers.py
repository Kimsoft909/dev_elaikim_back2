"""
Contact serializers matching Rust backend request/response structures.
"""
from rest_framework import serializers
from .models import Contact
from apps.core.utils import ValidationUtils


class CreateContactRequestSerializer(serializers.Serializer):
    """
    Contact creation request serializer matching Rust CreateContactRequest.
    """
    name = serializers.CharField(max_length=100, min_length=1)
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=200, min_length=1) 
    message = serializers.CharField(max_length=2000, min_length=1)
    
    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long")
        return value.strip()
    
    def validate_subject(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Subject must be at least 3 characters long")
        return value.strip()
    
    def validate_message(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long")
        return value.strip()


class UpdateContactStatusRequestSerializer(serializers.Serializer):
    """
    Contact status update serializer matching Rust UpdateContactStatusRequest.
    """
    status = serializers.ChoiceField(choices=Contact.StatusChoices.choices)
    reply_message = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['status'] == Contact.StatusChoices.REPLIED:
            reply_message = data.get('reply_message', '').strip()
            if not reply_message or len(reply_message) < 5:
                raise serializers.ValidationError(
                    "Reply message is required and must be at least 5 characters long when marking as replied"
                )
        return data


class ContactResponseSerializer(serializers.ModelSerializer):
    """
    Contact response serializer matching Rust ContactResponse.
    """
    class Meta:
        model = Contact
        fields = [
            'id', 'name', 'email', 'subject', 'message', 'status',
            'ip_address', 'user_agent', 'referrer', 'country',
            'reply_message', 'replied_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContactListResponseSerializer(serializers.Serializer):
    """
    Contact list response serializer matching Rust ContactListResponse.
    """
    contacts = ContactResponseSerializer(many=True)
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    per_page = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    unread_count = serializers.IntegerField()