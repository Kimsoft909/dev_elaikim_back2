# Django Backend Deployment Guide

## Production Deployment Checklist

### 1. Environment Variables Setup

Create a `.env` file with these required variables:

```bash
# Django Core
SECRET_KEY=your-very-long-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_SETTINGS_MODULE=portfolio_backend.settings.production

# Database (use DATABASE_URL for Render/Heroku)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Auto Superuser Creation
SUPERUSER_EMAIL=admin@yourdomain.com
SUPERUSER_USERNAME=admin
SUPERUSER_PASSWORD=secure_admin_password_123
SUPERUSER_FULL_NAME=System Administrator

# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_BUCKET_NAME=DevPort

# Redis Cache
REDIS_URL=redis://your-redis-url:6379

# Error Tracking
SENTRY_DSN=https://your-sentry-dsn
ENVIRONMENT=production

# Security
SECURE_SSL_REDIRECT=True
```

### 2. Database Migrations

Django will automatically handle migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Superuser Creation

The system automatically creates a superuser on startup if the environment variables are set and no superuser exists.

### 4. Server Configuration

**Using Daphne (Recommended):**
```bash
daphne portfolio_backend.asgi:application --port 8000 --bind 0.0.0.0
```

**Using Gunicorn (Alternative):**
```bash
gunicorn portfolio_backend.wsgi:application --bind 0.0.0.0:8000
```

### 5. Render Deployment

1. Connect your repository to Render
2. Use the provided `render.yaml` configuration
3. Set environment variables in Render dashboard
4. Deploy automatically triggers migrations and superuser creation

### 6. Health Monitoring

Two health endpoints are available:

- **Simple Health Check**: `GET /health/` (public, for UptimeRobot)
- **Detailed System Health**: `GET /api/v1/manage/system-health/` (authenticated, for admin)

### 7. Admin Interface Access

- **Django Admin**: `/admin/` (built-in Django admin)
- **API Management**: `/api/v1/manage/` (your custom admin API endpoints)

### 8. Static Files & Media

Configure static file serving in production:

```python
# In production settings
STATIC_ROOT = '/app/staticfiles'
MEDIA_ROOT = '/app/media'
```

### 9. Security Checklist

- ✅ SSL/HTTPS enabled
- ✅ Secret key secured
- ✅ Debug mode disabled
- ✅ CORS properly configured
- ✅ Rate limiting enabled
- ✅ SQL injection protection (Django ORM)
- ✅ XSS protection enabled
- ✅ CSRF protection enabled

### 10. Monitoring & Logging

- **Sentry**: Error tracking and performance monitoring
- **Logs**: Django logs to `/var/log/portfolio_backend/django.log`
- **Health Checks**: Both simple and detailed endpoints available
- **Performance**: Psutil system monitoring included

### 11. API Endpoints Overview

```
# Public Endpoints
GET  /health/                          # Simple health check
GET  /api/v1/public/projects/          # List projects
GET  /api/v1/public/projects/{id}/     # Get project
POST /api/v1/public/contact/           # Submit contact
GET  /api/v1/public/cv/download/       # Download CV

# Authentication
POST /api/v1/auth/login/               # Login
POST /api/v1/auth/refresh/             # Refresh token
POST /api/v1/auth/logout/              # Logout
POST /api/v1/auth/change-password/     # Change password
GET  /api/v1/auth/profile/             # Get profile
PUT  /api/v1/auth/profile/             # Update profile

# Management (Protected)
GET  /api/v1/manage/dashboard/         # Dashboard stats
GET  /api/v1/manage/system-health/     # System health
POST /api/v1/manage/projects/          # Create project
PUT  /api/v1/manage/projects/{id}/     # Update project
DELETE /api/v1/manage/projects/{id}/   # Delete project
GET  /api/v1/manage/contacts/          # List contacts
PUT  /api/v1/manage/contacts/{id}/     # Update contact
DELETE /api/v1/manage/contacts/{id}/   # Delete contact
```

### 12. Backup Strategy

Recommended backup approach:
- **Database**: Regular PostgreSQL backups
- **Media Files**: Supabase handles file storage and backups
- **Code**: Version control with Git
- **Environment**: Document all environment variables

### 13. Performance Optimization

- **Connection Pooling**: Enabled with django-pgconnpool
- **Redis Caching**: Configured for session and data caching
- **Static Files**: Collected and served efficiently
- **Database Queries**: Optimized with select_related and prefetch_related
- **Rate Limiting**: Protects against abuse

This deployment guide ensures a production-ready Django backend with proper security, monitoring, and performance optimization.