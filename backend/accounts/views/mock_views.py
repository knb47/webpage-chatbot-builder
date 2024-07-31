from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from ..serializers import UserSerializer, FileUploadSerializer, DeploymentSerializer
from ..models import UploadedFile, Deployment
from ..forms import FileUploadForm, CustomUserCreationForm
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

class CreateUserView(generics.CreateAPIView):
    model = get_user_model()
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

@method_decorator(login_required, name='dispatch')
class FileUploadView(View):
    def get(self, request):
        print("GET request received")
        form = FileUploadForm()
        print("Rendering upload form")
        return render(request, 'upload.html', {'form': form})

    def post(self, request):
        print("POST request received")
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            file_name = file.name
            print(f"Uploading file with name: {file_name}")
            newfile = UploadedFile(file=file, file_name=file_name, user=request.user)
            newfile.save()
            print(f"Saved file with ID: {newfile.id}, name: {newfile.file_name}")
            return redirect('library')
        else:
            print("Form is not valid")
            print(f"Form errors: {form.errors}")
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
        print(f"Retrieved file with name: {file.file_name}")  # Debugging statement
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
    chatbot_name = "MyChatbot"  # Replace with actual chatbot name if available
    endpoint = 'http://example.com/endpoint'  # Replace with actual endpoint if available

    # Mock the deployment process
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
