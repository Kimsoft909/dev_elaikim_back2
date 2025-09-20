"""
Project serializers matching Rust request/response structures.
"""
from rest_framework import serializers
from .models import Project, ProjectImage
from apps.core.utils import ValidationUtils


class ProjectImageResponseSerializer(serializers.ModelSerializer):
    """Matches Rust ProjectImageResponse struct."""
    
    class Meta:
        model = ProjectImage
        fields = ['id', 'url', 'is_primary', 'original_name']


class CreateProjectRequestSerializer(serializers.Serializer):
    """Matches Rust CreateProjectRequest struct."""
    title = serializers.CharField(min_length=1, max_length=200)
    description = serializers.CharField(min_length=1, max_length=500)
    long_description = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    technologies = serializers.JSONField()
    features = serializers.JSONField()
    github_url = serializers.URLField(required=False, allow_blank=True)
    live_url = serializers.URLField(required=False, allow_blank=True)
    duration = serializers.CharField(max_length=100, required=False, allow_blank=True)
    team_size = serializers.CharField(max_length=100, required=False, allow_blank=True)
    year = serializers.CharField(min_length=4, max_length=4)
    is_featured = serializers.BooleanField(required=False, default=False)
    sort_order = serializers.IntegerField(required=False, default=0)
    
    def validate_year(self, value):
        """Validate year format and range."""
        if not ValidationUtils.validate_year(value):
            raise serializers.ValidationError("Invalid year. Must be a 4-digit year between 2000 and next year.")
        return value
    
    def validate_technologies(self, value):
        """Validate technologies is a list of strings."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Technologies must be a list")
        
        for tech in value:
            if not isinstance(tech, str):
                raise serializers.ValidationError("All technologies must be strings")
            if len(tech.strip()) == 0:
                raise serializers.ValidationError("Technology names cannot be empty")
        
        return value
    
    def validate_features(self, value):
        """Validate features is a list of strings."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Features must be a list")
        
        for feature in value:
            if not isinstance(feature, str):
                raise serializers.ValidationError("All features must be strings")
            if len(feature.strip()) == 0:
                raise serializers.ValidationError("Feature descriptions cannot be empty")
        
        return value


class UpdateProjectRequestSerializer(serializers.Serializer):
    """Matches Rust UpdateProjectRequest struct."""
    title = serializers.CharField(min_length=1, max_length=200, required=False)
    description = serializers.CharField(min_length=1, max_length=500, required=False)
    long_description = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    technologies = serializers.JSONField(required=False)
    features = serializers.JSONField(required=False)
    github_url = serializers.URLField(required=False, allow_blank=True)
    live_url = serializers.URLField(required=False, allow_blank=True)
    duration = serializers.CharField(max_length=100, required=False, allow_blank=True)
    team_size = serializers.CharField(max_length=100, required=False, allow_blank=True)
    year = serializers.CharField(min_length=4, max_length=4, required=False)
    is_featured = serializers.BooleanField(required=False)
    sort_order = serializers.IntegerField(required=False)
    
    def validate_year(self, value):
        """Validate year format and range."""
        if not ValidationUtils.validate_year(value):
            raise serializers.ValidationError("Invalid year. Must be a 4-digit year between 2000 and next year.")
        return value
    
    def validate_technologies(self, value):
        """Validate technologies is a list of strings."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Technologies must be a list")
        
        for tech in value:
            if not isinstance(tech, str):
                raise serializers.ValidationError("All technologies must be strings")
            if len(tech.strip()) == 0:
                raise serializers.ValidationError("Technology names cannot be empty")
        
        return value
    
    def validate_features(self, value):
        """Validate features is a list of strings."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Features must be a list")
        
        for feature in value:
            if not isinstance(feature, str):
                raise serializers.ValidationError("All features must be strings")
            if len(feature.strip()) == 0:
                raise serializers.ValidationError("Feature descriptions cannot be empty")
        
        return value


class ProjectResponseSerializer(serializers.ModelSerializer):
    """Matches Rust ProjectResponse struct."""
    technologies = serializers.ListField(child=serializers.CharField())
    features = serializers.ListField(child=serializers.CharField())
    images = ProjectImageResponseSerializer(many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'long_description',
            'technologies', 'features', 'github_url', 'live_url',
            'duration', 'team_size', 'year', 'images', 'demo_video_url',
            'is_featured', 'created_at', 'updated_at'
        ]


class ProjectListSerializer(serializers.ModelSerializer):
    """Serializer for project list views (lighter version)."""
    technologies = serializers.ListField(child=serializers.CharField())
    features = serializers.ListField(child=serializers.CharField())
    primary_image = ProjectImageResponseSerializer(read_only=True)
    images = ProjectImageResponseSerializer(many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'technologies', 'features',
            'github_url', 'live_url', 'year', 'primary_image', 'images',
            'demo_video_url', 'is_featured', 'created_at'
        ]