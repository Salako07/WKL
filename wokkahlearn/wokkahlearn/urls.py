# wokkahlearn/urls.py - Updated with all apps
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health check
    path('health/', include('health_check.urls')),
    
    # Authentication
    path('api/auth/', include('accounts.urls')),
    
    # Main API endpoints
    path('api/', include('api.urls')),
    
    # Individual app APIs
    path('api/courses/', include('courses.urls')),
    path('api/ai-tutor/', include('ai_tutor.urls')),
   # path('api/code-execution/', include('code_execution.urls')),
    #path('api/collaboration/', include('collaboration.urls')),
    #path('api/analytics/', include('analytics.urls')),
    
    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# API Error Handlers
handler400 = 'api.views.bad_request'
handler403 = 'api.views.permission_denied'
handler404 = 'api.views.not_found'
handler500 = 'api.views.server_error'