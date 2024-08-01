from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from ..serializers import UserSerializer, FileUploadSerializer, DeploymentSerializer
from ..models import UploadedFile, Deployment, EmailLog
from ..forms import FileUploadForm, CustomUserCreationForm
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
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            file_name = file.name
            newfile = UploadedFile(file=file, file_name=file_name, user=request.user)
            newfile.save()
            return redirect('library')
        return render(request, 'upload.html', {'form': form})

class FileListView(generics.ListAPIView):
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UploadedFile.objects.filter(user=self.request.user)

@login_required
def delete_file_view(request, file_id):
    if request.method == 'POST':
        file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
        file.file.delete()
        file.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@login_required
def library_view(request):
    files = UploadedFile.objects.filter(user=request.user)
    for file in files:
        file.deployed = Deployment.objects.filter(config_file_name=file.file_name, user=request.user).exists()
    return render(request, 'library.html', {'files': files})

@login_required
def home_view(request):
    return render(request, 'home.html')

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('home')
    template_name = 'signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(self.request, user)
            logger.info(f'User {username} signed up and logged in successfully.')
        else:
            logger.error(f'User {username} could not be authenticated after sign-up.')
        return response

def custom_logout(request):
    logout(request)
    return redirect('login')

@login_required
def deploy_view(request, file_id):
    config_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    chatbot_name = "MyChatbot"
    endpoint = 'http://example.com/endpoint'
    deployment = Deployment.objects.create(
        user=request.user,
        config_file_name=config_file.file.name,
        chatbot_name=chatbot_name,
        endpoint=endpoint,
        status='completed'
    )
    return JsonResponse({'task_id': deployment.id})

@login_required
def deployment_status_view(request, task_id):
    deployment = get_object_or_404(Deployment, id=task_id, user=request.user)
    return JsonResponse({
        'status': 'completed',
        'endpoint': deployment.endpoint,
        'config_file_name': deployment.config_file_name,
        'config_file_id': deployment.id
    })

@login_required
def deployments_view(request):
    deployments = Deployment.objects.filter(user=request.user)
    return render(request, 'deployments.html', {'deployments': deployments})

@login_required
def delete_deployment_view(request, deployment_id):
    if request.method == 'POST':
        deployment = get_object_or_404(Deployment, id=deployment_id, user=request.user)
        deployment.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

def password_reset_request(request):
    if request.method == 'POST':
        print("Password reset POST request received")  # Debugging
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            print(f"Form is valid. Email: {email}")  # Debugging
            user = get_user_model().objects.filter(email=email).first()
            if user:
                print(f"User found: {user}")  # Debugging
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
                try:
                    send_mail(mail_subject, message, settings.DEFAULT_FROM_EMAIL, [email])
                    EmailLog.objects.create(recipient=email, subject=mail_subject, body=message, success=True)
                    logger.info(f'Password reset email sent to {email}')
                    print("Password reset email sent")  # Debugging
                    return redirect('password_reset_done')
                except BadHeaderError:
                    EmailLog.objects.create(recipient=email, subject=mail_subject, body=message, success=False, error_message='Invalid header found.')
                    logger.error(f'Invalid header found while sending password reset email to {email}')
                    print("BadHeaderError occurred")  # Debugging
                except Exception as e:
                    EmailLog.objects.create(recipient=email, subject=mail_subject, body=message, success=False, error_message=str(e))
                    logger.error(f'Error sending password reset email to {email}: {e}')
                    print(f"Exception occurred: {e}")  # Debugging
            else:
                print(f"No user found with email: {email}")  # Debugging
        else:
            print("Form is not valid")  # Debugging
    else:
        form = PasswordResetForm()
        print("Password reset form requested")  # Debugging
    return render(request, 'password_reset.html', {'form': form})
