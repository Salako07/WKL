import os
import sys

def diagnose_django_setup():
    """Diagnose Django configuration issues"""
    print("🔍 Diagnosing Django setup...\n")
    
    # Check 1: Python path
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print()
    
    # Check 2: Django installation
    try:
        import django
        print(f"✅ Django version: {django.get_version()}")
    except ImportError:
        print("❌ Django not installed!")
        return
    
    # Check 3: Settings module
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wokkahlearn.settings')
        django.setup()
        print("✅ Django settings loaded successfully")
    except Exception as e:
        print(f"❌ Django settings error: {e}")
        return
    
    # Check 4: Apps
    from django.apps import apps
    app_configs = apps.get_app_configs()
    print(f"✅ Found {len(app_configs)} Django apps:")
    for app in app_configs:
        print(f"   - {app.label}")
    print()
    
    # Check 5: Database
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection working")
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    # Check 6: URLs
    try:
        from django.urls import get_resolver
        resolver = get_resolver()
        print("✅ URL configuration loaded")
    except Exception as e:
        print(f"❌ URL configuration error: {e}")
    
    print("\n🎉 Django diagnosis completed!")

if __name__ == "__main__":
    diagnose_django_setup()


# 5. Check if all required files exist - save as check_files.py
import os

def check_required_files():
    """Check if all required Django files exist"""
    print("📁 Checking required files...\n")
    
    required_files = [
        'manage.py',
        'wokkahlearn/__init__.py',
        'wokkahlearn/settings.py', 
        'wokkahlearn/urls.py',
        'wokkahlearn/wsgi.py',
        'wokkahlearn/asgi.py',
        'accounts/__init__.py',
        'accounts/models.py',
        'accounts/apps.py',
        'courses/__init__.py',
        'courses/models.py',
        'courses/apps.py',
        'api/__init__.py',
        'api/urls.py',
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING!")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n🚨 Missing {len(missing_files)} required files!")
        print("Create these files to fix the issue.")
    else:
        print("\n🎉 All required files exist!")

if __name__ == "__main__":
    check_required_files()

