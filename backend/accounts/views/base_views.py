# backend/accounts/views.py

from ..serializers import UserSerializer, FileUploadSerializer, DeploymentSerializer
from ..models import UploadedFile, Deployment, EmailLog
from ..forms import FileUploadForm, CustomUserCreationForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.core.mail import send_mail, BadHeaderError
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.forms import PasswordResetForm
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class CreateUserView(generics.CreateAPIView):
    model = get_user_model()
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

@method_decorator(login_required, name='dispatch')
class FileUploadView(View):
    def get(self, request):
        form = FileUploadForm()
        return render(request, 'upload.html', {'form': form})

    def post(self, request):
        try:
            logger.debug(f"User {request.user.id} uploading file.")
        except Exception as e:
            print(f"Logging failed: {e}")
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            # The relative path is stored automatically by Django's FileField
            file_path = file.name  # This gives us the relative path as stored
            file_name = file.name.split('/')[-1]  # Extract the file name from the path
            logger.debug(f"File path: {file_path}, File name: {file_name}")

            newfile = UploadedFile(file=file, file_name=file_name, user=request.user)
            newfile.save()

            logger.info(f"File uploaded with path: {file_path} and name: {file_name} by user: {request.user.id}")

            return redirect('library')
        return render(request, 'upload.html', {'form': form})

class FileListView(generics.ListAPIView):
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UploadedFile.objects.filter(user=self.request.user)

@login_required
def delete_file(request, file_id):
    if request.method == 'POST':
        try:
            file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
            file.file.delete()  # Delete the file from storage
            file.delete()  # Delete the file entry from the database
            logger.info(f'File {file.file_name} deleted by user {request.user.username}.')
            return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f'Error deleting file {file_id}: {e}')
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False}, status=400)

@login_required
def library_view(request):
    files = UploadedFile.objects.filter(user=request.user)
    for file in files:
        file.deployed = Deployment.objects.filter(config_file_path=file.file_name, user=request.user).exists()
    return render(request, 'library.html', {'files': files})

@login_required
def home_view(request):
    return render(request, 'home.html')

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

def custom_logout(request):
    logout(request)
    return redirect('login')
    
@login_required
def deployments_view(request):
    deployments = Deployment.objects.filter(user=request.user)
    return render(request, 'deployments.html', {'deployments': deployments})

@login_required
def delete_deployment(request, deployment_id):
    if request.method == 'POST':
        deployment = get_object_or_404(Deployment, id=deployment_id, user=request.user)
        deployment.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = get_user_model().objects.filter(email=email).first()
            if user:
                try:
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    current_site = get_current_site(request)
                    mail_subject = 'Reset your password'
                    message = render_to_string('password_reset_email.html', {
                        'user': user,
                        'domain': current_site.domain,
                        'uid': uid,
                        'token': token,
                    })
                    send_mail(mail_subject, message, settings.DEFAULT_FROM_EMAIL, [email])
                    EmailLog.objects.create(recipient=email, subject=mail_subject, body=message, success=True)
                    logger.info(f'Password reset email sent to {email}')
                    return redirect('password_reset_done')
                except BadHeaderError:
                    EmailLog.objects.create(recipient=email, subject=mail_subject, body=message, success=False, error_message='Invalid header found.')
                    logger.error(f'Invalid header found while sending password reset email to {email}')
                except Exception as e:
                    EmailLog.objects.create(recipient=email, subject=mail_subject, body=message, success=False, error_message=str(e))
                    logger.error(f'Error sending password reset email to {email}: {e}')
    else:
        form = PasswordResetForm()
    return render(request, 'password_reset.html', {'form': form})