# Django Portfolio Backend

This is a Django backend that replicates the exact functionality of the Rust portfolio backend, maintaining the same API endpoints, data structures, and file storage patterns.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Supabase account

### 1. Setup Environment

```bash
# Clone and navigate to Django backend
cd Django_back

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your actual values:
# - Database credentials
# - Supabase URL and key
# - Redis URL
# - Secret key
```

### 3. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create admin user (interactive)
python manage.py create_admin

# Or non-interactive
python manage.py create_admin --email admin@example.com --username admin --non-interactive
```

### 4. Run Development Server

```bash
# Start Redis (if not already running)
redis-server

# Start Django development server
python manage.py runserver
```

### 5. Production Deployment

```bash
# Using Docker Compose
docker-compose up -d

# Or manual deployment
gunicorn portfolio_backend.asgi:application -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📋 API Endpoints

All endpoints match the Rust backend exactly:

### Public Endpoints
- `GET /api/v1/public/projects` - Get all projects
- `GET /api/v1/public/projects/{id}` - Get single project  
- `POST /api/v1/public/contact` - Submit contact form
- `GET /api/v1/public/cv/download` - Download CV PDF

### Auth Endpoints
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh JWT token
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/change-password` - Change password
- `GET /api/v1/auth/profile` - Get user profile
- `PUT /api/v1/auth/profile` - Update user profile

### Admin Endpoints (Protected)
- `GET /api/v1/admin/dashboard` - Dashboard statistics
- `POST /api/v1/admin/projects` - Create project
- `PUT /api/v1/admin/projects/{id}` - Update project
- `DELETE /api/v1/admin/projects/{id}` - Delete project
- `GET /api/v1/admin/contacts` - Get all contacts
- `PUT /api/v1/admin/contacts/{id}` - Update contact status
- `DELETE /api/v1/admin/contacts/{id}` - Delete contact
- `GET /api/v1/admin/health` - System health check

## 🎯 Key Features

### Performance Optimizations
- ✅ ASGI with Uvicorn workers
- ✅ PostgreSQL connection pooling  
- ✅ Redis caching (view-level and query-level)
- ✅ Database query optimization
- ✅ Rate limiting middleware
- ✅ Async views for I/O operations
- ✅ Celery for background tasks

### Security
- ✅ JWT authentication (1-hour access, 7-day refresh)
- ✅ Argon2 password hashing
- ✅ Account lockout after failed attempts
- ✅ Rate limiting (60 req/min, burst of 10)
- ✅ CORS configuration
- ✅ Security headers

### File Storage
- ✅ Supabase integration for images and videos
- ✅ File validation and size limits
- ✅ Automatic cleanup on deletion

### Monitoring
- ✅ Comprehensive logging
- ✅ Health check endpoints
- ✅ Sentry integration (optional)
- ✅ Performance metrics

## 🔧 Management Commands

```bash
# Create admin user
python manage.py create_admin

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Clear cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

## 📦 Tech Stack

- **Framework**: Django 5.0 + Django REST Framework
- **Database**: PostgreSQL with connection pooling
- **Cache**: Redis
- **Authentication**: JWT with SimpleJWT
- **File Storage**: Supabase Storage
- **Background Tasks**: Celery + Redis
- **Deployment**: Docker + Docker Compose
- **Monitoring**: Sentry (optional)

This Django backend maintains 100% API compatibility with the Rust version while providing the same performance characteristics through careful optimization.