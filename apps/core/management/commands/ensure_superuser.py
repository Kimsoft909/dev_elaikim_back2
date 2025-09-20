"""
Django management command to auto-create superuser from environment variables.
Runs automatically on server startup without user interaction.
"""
import os
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from decouple import config

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Auto-create superuser from environment variables if not exists'
    
    def handle(self, *args, **options):
        """Create superuser from environment variables."""
        try:
            # Get required environment variables
            superuser_email = config('SUPERUSER_EMAIL', default=None)
            superuser_username = config('SUPERUSER_USERNAME', default=None)
            superuser_password = config('SUPERUSER_PASSWORD', default=None)
            superuser_full_name = config('SUPERUSER_FULL_NAME', default='')
            
            # Check if all required fields are provided
            missing_vars = []
            if not superuser_email:
                missing_vars.append('SUPERUSER_EMAIL')
            if not superuser_username:
                missing_vars.append('SUPERUSER_USERNAME')
            if not superuser_password:
                missing_vars.append('SUPERUSER_PASSWORD')
            
            if missing_vars:
                self.stdout.write(
                    self.style.WARNING(
                        f'Superuser creation skipped. Missing environment variables: {", ".join(missing_vars)}'
                    )
                )
                return
            
            # Validate email format
            try:
                validate_email(superuser_email)
            except ValidationError:
                self.stdout.write(
                    self.style.ERROR(
                        f'Superuser creation failed: Invalid email format: {superuser_email}'
                    )
                )
                return
            
            # Check if superuser already exists
            if User.objects.filter(email=superuser_email).exists():
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Superuser with email {superuser_email} already exists. Skipping creation.'
                    )
                )
                return
            
            if User.objects.filter(username=superuser_username).exists():
                self.stdout.write(
                    self.style.ERROR(
                        f'Superuser creation failed: Username {superuser_username} already exists'
                    )
                )
                return
            
            # Validate password strength
            if len(superuser_password) < 8:
                self.stdout.write(
                    self.style.ERROR(
                        'Superuser creation failed: Password must be at least 8 characters long'
                    )
                )
                return
            
            # Create superuser
            user = User.objects.create_superuser(
                email=superuser_email,
                username=superuser_username,
                password=superuser_password,
                full_name=superuser_full_name,
                is_admin=True,
                is_staff=True,
                is_superuser=True
            )
            
            # Success message
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Superuser created successfully!'
                )
            )
            self.stdout.write(f'   Email: {user.email}')
            self.stdout.write(f'   Username: {user.username}')
            self.stdout.write(f'   Full Name: {user.full_name or "Not provided"}')
            self.stdout.write(f'   User ID: {user.id}')
            self.stdout.write(
                self.style.SUCCESS(
                    '   ✅ You can now login to the admin panel with these credentials.\n'
                )
            )
            
            logger.info(f'Superuser created: {user.email} (ID: {user.id})')
            
        except Exception as e:
            error_msg = f'Error creating superuser: {str(e)}'
            self.stdout.write(self.style.ERROR(error_msg))
            logger.error(error_msg, exc_info=True)