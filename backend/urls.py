"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static

# Conditional import based on environment
print(f"settings.DEBUG: {settings.DEBUG}")
if settings.DEBUG:
    from backend.accounts.views import mock_views as views
else:
    from backend.accounts.views import prod_views as views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/accounts/', include('backend.accounts.urls')),
    
    # Authentication views
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Home page
    path('', views.home_view, name='home'),
    
    # Include other account-related URLs
    path('account/', include('backend.accounts.urls')),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
