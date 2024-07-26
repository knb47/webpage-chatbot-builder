from django.urls import path
from .views import FileUploadView, FileListView, library_view, CreateUserView, SignUpView

urlpatterns = [
    # API routes
    path('register/', CreateUserView.as_view(), name='account-create'),
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('files/', FileListView.as_view(), name='file-list'),
    
    # Non-API routes
    path('library/', library_view, name='library'),
    # Add any other account-specific routes here,
    path('signup/', SignUpView.as_view(), name='signup'),
    path('upload/', FileUploadView.as_view(), name='file-upload'),
]