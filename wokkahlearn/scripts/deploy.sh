#!/bin/bash

# WokkahLearn Deployment Script
set -e

echo "🚀 Starting WokkahLearn deployment..."

# Configuration
ENVIRONMENT=${1:-development}
DOCKER_REGISTRY=${DOCKER_REGISTRY:-wokkahlearn}
VERSION=${VERSION:-latest}

echo "📦 Environment: $ENVIRONMENT"
echo "📦 Version: $VERSION"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
echo "🔍 Checking required tools..."
for tool in docker docker-compose git; do
    if ! command_exists $tool; then
        echo "❌ $tool is required but not installed."
        exit 1
    fi
done

# Load environment variables
if [ -f ".env.$ENVIRONMENT" ]; then
    echo "📋 Loading environment variables from .env.$ENVIRONMENT"
    set -a
    source .env.$ENVIRONMENT
    set +a
else
    echo "⚠️  .env.$ENVIRONMENT file not found, using defaults"
fi

# Build and tag images
echo "🏗️  Building Docker images..."
docker-compose -f docker-compose.yml -f docker-compose.$ENVIRONMENT.yml build

# Tag images for registry
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🏷️  Tagging images for production..."
    docker tag wokkahlearn_backend:latest $DOCKER_REGISTRY/backend:$VERSION
    docker tag wokkahlearn_frontend:latest $DOCKER_REGISTRY/frontend:$VERSION
    docker tag wokkahlearn_code_executor:latest $DOCKER_REGISTRY/code-executor:$VERSION
    
    # Push to registry
    echo "📤 Pushing images to registry..."
    docker push $DOCKER_REGISTRY/backend:$VERSION
    docker push $DOCKER_REGISTRY/frontend:$VERSION
    docker push $DOCKER_REGISTRY/code-executor:$VERSION
fi

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.yml -f docker-compose.$ENVIRONMENT.yml run --rm backend python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
docker-compose -f docker-compose.yml -f docker-compose.$ENVIRONMENT.yml run --rm backend python manage.py collectstatic --noinput

# Create superuser (only in development)
if [ "$ENVIRONMENT" = "development" ]; then
    echo "👤 Creating superuser..."
    docker-compose -f docker-compose.yml -f docker-compose.$ENVIRONMENT.yml run --rm backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@wokkahlearn.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"
fi

# Start services
echo "🚀 Starting services..."
docker-compose -f docker-compose.yml -f docker-compose.$ENVIRONMENT.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Health check
echo "🏥 Performing health checks..."
if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    exit 1
fi

if curl -f http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
    exit 1
fi

echo "🎉 Deployment completed successfully!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000/api"
echo "👑 Admin Panel: http://localhost:8000/admin"

if [ "$ENVIRONMENT" = "development" ]; then
    echo "📊 Grafana: http://localhost:3001 (admin/admin123)"
    echo "📈 Prometheus: http://localhost:9090"
fi

echo "📝 Check logs with: docker-compose logs -f"
echo "🛑 Stop services with: docker-compose down"