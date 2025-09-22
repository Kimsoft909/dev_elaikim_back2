#!/usr/bin/env bash
set -e  # Exit on any error

echo "🚀 Starting Django build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Set Django settings for production
export DJANGO_SETTINGS_MODULE=portfolio_backend.settings.production

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

# Create superuser if environment variables are set
echo "👤 Creating superuser if needed..."
python manage.py ensure_superuser

echo "✅ Build completed successfully!"
