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
from django.contrib.auth import views as auth_views
from backend.accounts.views import home_view, custom_logout

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/accounts/', include('backend.accounts.urls')),
    
    # Authentication views
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),  # Add this line
    path('logout/', custom_logout, name='logout'),
    
    # Home page
    path('', home_view, name='home'),
    
    # Include other account-related URLs
    path('', include('backend.accounts.urls')),  # Changed from 'accounts/' to ''
]