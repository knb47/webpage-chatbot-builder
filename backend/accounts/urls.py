from django.urls import path
from django.conf import settings
import os

if os.getenv('DJANGO_ENV') == 'production':
  import backend.accounts.views.prod_views as views
else:
  import backend.accounts.views.mock_views as views

urlpatterns = [
  # API routes
  path('register/', views.CreateUserView.as_view(), name='account-create'),
  path('upload/', views.FileUploadView.as_view(), name='file-upload'),
  path('files/', views.FileListView.as_view(), name='file-list'),
  path('deploy/<int:file_id>/', views.deploy_view, name='deploy'),
  path('deployment_status/<str:task_id>/', views.deployment_status_view, name='deployment_status'),
  path('deployments/', views.deployments_view, name='deployments'),
  
  # Non-API routes
  path('library/', views.library_view, name='library'),
  path('signup/', views.SignUpView.as_view(), name='signup'),
  path('upload/', views.FileUploadView.as_view(), name='file-upload'),
  path('update_chatbot_name/<int:file_id>/', views.UpdateChatbotNameView.as_view(), name='update_chatbot_name'),
  path('delete-file/<int:file_id>/', views.delete_file, name='delete_file'),
  path('delete-deployment/<int:deployment_id>/', views.delete_deployment, name='delete_deployment'),
  path('teardown/<int:deployment_id>/', views.teardown_view, name='teardown'),
  path('teardown_status/<str:task_id>/', views.teardown_status_view, name='teardown_status'),
]
