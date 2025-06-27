# WokkahLearn Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+ (if running locally)
- Redis 7+ (if running locally)

## Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/wokkahlearn.git
   cd wokkahlearn
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the application**
   ```bash
   chmod +x scripts/deploy.sh
   ./scripts/deploy.sh development
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api
   - Admin Panel: http://localhost:8000/admin
   - API Documentation: http://localhost:8000/api/schema/swagger-ui/

## Manual Setup

### Backend Setup

1. **Create virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up database**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic
   ```

4. **Run development server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**
   ```bash
   npm start
   ```

### Additional Services

1. **Start Celery worker** (in separate terminal)
   ```bash
   cd backend
   celery -A wokkahlearn worker --loglevel=info
   ```

2. **Start Celery beat** (in separate terminal)
   ```bash
   cd backend
   celery -A wokkahlearn beat --loglevel=info
   ```

## Configuration

### Database Configuration

For PostgreSQL:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'wokkahlearn',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### AI Service Configuration

1. **OpenAI Configuration**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

2. **Anthropic Configuration**
   ```bash
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   ```

### Code Execution Setup

1. **Docker Network**
   ```bash
   docker network create wokkahlearn_execution
   ```

2. **Pull execution environments**
   ```bash
   docker pull python:3.11-alpine
   docker pull node:18-alpine
   docker pull openjdk:17-alpine
   ```

## Testing

### Backend Tests
```bash
cd backend
python manage.py test
# or with coverage
coverage run --source='.' manage.py test
coverage report
```

### Frontend Tests
```bash
cd frontend
npm test
# or with coverage
npm run test:coverage
```

### E2E Tests
```bash
cd e2e
npx cypress run
# or interactive mode
npx cypress open
```

## Deployment

### Production Environment

1. **Set production environment variables**
   ```bash
   export DEBUG=False
   export SECRET_KEY="your-production-secret-key"
   export ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"
   ```

2. **Set up SSL certificates**
   ```bash
   certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

3. **Deploy with Docker Compose**
   ```bash
   ./scripts/deploy.sh production
   ```

### Kubernetes Deployment

1. **Apply configurations**
   ```bash
   kubectl apply -f kubernetes/namespace.yaml
   kubectl apply -f kubernetes/configmap.yaml
   kubectl apply -f kubernetes/secret.yaml
   kubectl apply -f kubernetes/
   ```

2. **Verify deployment**
   ```bash
   kubectl get pods -n wokkahlearn
   kubectl get services -n wokkahlearn
   ```

## Monitoring

### Health Checks

- Backend: http://localhost:8000/health/
- Frontend: http://localhost:3000/health
- Database: Check connection in Django admin

### Monitoring Stack

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin123)

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check PostgreSQL is running
   - Verify credentials in .env file
   - Ensure database exists

2. **Frontend build errors**
   - Clear node_modules and reinstall
   - Check Node.js version compatibility
   - Verify environment variables

3. **Code execution timeouts**
   - Check Docker daemon is running
   - Verify network configuration
   - Review container resource limits

4. **WebSocket connection issues**
   - Check Redis is running
   - Verify CORS configuration
   - Review proxy settings

### Performance Optimization

1. **Database**
   - Add indexes for frequently queried fields
   - Use database connection pooling
   - Implement query optimization

2. **Frontend**
   - Enable code splitting
   - Implement lazy loading
   - Use service workers for caching

3. **Backend**
   - Configure Gunicorn workers
   - Implement Redis caching
   - Use CDN for static files

## Security

### Production Security Checklist

- [ ] Change default passwords
- [ ] Configure HTTPS
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Configure CORS properly
- [ ] Set secure headers
- [ ] Regular security updates
- [ ] Backup strategy implemented

### API Security

- JWT token expiration: 1 hour
- Refresh token rotation enabled
- Rate limiting: 1000 requests/hour per user
- Input validation on all endpoints
- SQL injection protection
- XSS protection enabled

## Support

For additional help:
- Check the [FAQ](docs/FAQ.md)
- Review [API Documentation](docs/API.md)
- Submit issues on GitHub
- Contact support at support@wokkahlearn.com