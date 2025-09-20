"""
Project views matching Rust handler endpoints.
"""
import logging
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Project, ProjectImage
from .serializers import (
    CreateProjectRequestSerializer, UpdateProjectRequestSerializer,
    ProjectResponseSerializer, ProjectListSerializer
)
from apps.core.utils import ApiResponse, PaginationUtils
from apps.core.services import supabase_service

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_projects(request):
    """GET /api/v1/public/projects - Get all projects with caching"""
    cache_key = 'projects_list'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return ApiResponse.success(cached_data)
    
    projects = Project.objects.select_related().prefetch_related('images').all()
    serializer = ProjectListSerializer(projects, many=True)
    
    # Cache for 5 minutes
    cache.set(cache_key, serializer.data, 300)
    
    return ApiResponse.success(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_project(request, project_id):
    """GET /api/v1/public/projects/{id} - Get single project"""
    project = get_object_or_404(Project, id=project_id)
    serializer = ProjectResponseSerializer(project)
    return ApiResponse.success(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_project(request):
    """POST /api/v1/admin/projects - Create new project"""
    serializer = CreateProjectRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return ApiResponse.validation_error(serializer.errors)
    
    # Create project
    project = Project.objects.create(**serializer.validated_data)
    
    # Handle file uploads to Supabase
    for file in request.FILES.getlist('images'):
        try:
            # Upload to Supabase using upload_image method
            result = supabase_service.upload_image(
                file, 
                project_id=str(project.id),
                is_primary=not project.images.exists()
            )
            
            if not result.get('success'):
                logger.error(f"Failed to upload image {file.name}: {result.get('error')}")
                continue
                
            file_url = result['url']
            
            # Create ProjectImage record
            ProjectImage.objects.create(
                project=project,
                filename=f"{project.id}_{file.name}",
                original_name=file.name,
                url=file_url,
                file_size=file.size,
                mime_type=file.content_type,
                is_primary=not project.images.exists()  # First image is primary
            )
        except Exception as e:
            logger.error(f"Failed to upload image {file.name}: {e}")
    
    # Handle demo video upload
    if 'demo_video' in request.FILES:
        video_file = request.FILES['demo_video']
        try:
            result = supabase_service.upload_video(
                video_file,
                project_id=str(project.id)
            )
            
            if result.get('success'):
                project.demo_video_url = result['url']
                project.save()
            else:
                logger.error(f"Failed to upload video: {result.get('error')}")
        except Exception as e:
            logger.error(f"Failed to upload video: {e}")
    
    # Clear projects cache
    cache.delete('projects_list')
    
    response_serializer = ProjectResponseSerializer(project)
    return ApiResponse.success(response_serializer.data, "Project created successfully")


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_project(request, project_id):
    """PUT /api/v1/admin/projects/{id} - Update project"""
    project = get_object_or_404(Project, id=project_id)
    
    serializer = UpdateProjectRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return ApiResponse.validation_error(serializer.errors)
    
    # Update project fields
    for field, value in serializer.validated_data.items():
        setattr(project, field, value)
    
    project.save()
    
    response_serializer = ProjectResponseSerializer(project)
    return ApiResponse.success(response_serializer.data, "Project updated successfully")


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_project(request, project_id):
    """DELETE /api/v1/admin/projects/{id} - Delete project"""
    project = get_object_or_404(Project, id=project_id)
    
    # Delete associated files from Supabase
    try:
        # Delete project images
        for image in project.images.all():
            file_path = f"images/{project.id}/{image.filename}"
            supabase_service.delete_file(file_path)
        
        # Delete demo video if exists
        if project.demo_video_url:
            # Extract filename from URL and delete
            video_filename = project.demo_video_url.split('/')[-1]
            video_path = f"videos/{project.id}/{video_filename}"
            supabase_service.delete_file(video_path)
    except Exception as e:
        logger.error(f"Failed to delete project files: {e}")
    
    project.delete()
    
    # Clear projects cache
    cache.delete('projects_list')
    
    return ApiResponse.success(message="Project deleted successfully")