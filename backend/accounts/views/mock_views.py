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
            newfile = UploadedFile(file=request.FILES['file'], user=request.user)
            newfile.save()
            return redirect('library')
        return render(request, 'upload.html', {'form': form})

class FileListView(generics.ListAPIView):
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UploadedFile.objects.filter(user=self.request.user)

@login_required
def upload_view(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            newfile = UploadedFile(file=request.FILES['file'], user=request.user)
            newfile.save()
            return redirect('library')
    else:
        form = FileUploadForm()
    return render(request, 'accounts/upload.html', {'form': form})

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
        file.deployed = Deployment.objects.filter(config_file=file, user=request.user).exists()
    return render(request, 'library.html', {'files': files})

@login_required
def home_view(request):
    return render(request, 'home.html')

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        # Authenticate and log the user in
        user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
        if user is not None:
            login(self.request, user)
        return response

def custom_logout(request):
    logout(request)
    return redirect('login')

@login_required
def deploy_view(request, file_id):
    config_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    # Mock the deployment process
    deployment = Deployment.objects.create(
        user=request.user,
        config_file=config_file,
        endpoint='http://example.com/endpoint',
        status='completed'
    )
    return JsonResponse({'task_id': deployment.id})

@login_required
def deployment_status_view(request, task_id):
    deployment = get_object_or_404(Deployment, id=task_id, user=request.user)
    return JsonResponse({
        'status': 'completed',
        'endpoint': deployment.endpoint,
        'config_file_name': deployment.config_file.file.name,
        'config_file_id': deployment.config_file.id
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
