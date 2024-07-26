from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import UserSerializer, FileUploadSerializer
from .models import UploadedFile
from .forms import FileUploadForm  # Ensure this is defined in forms.py
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .forms import CustomUserCreationForm
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
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

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('library')
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})
    return render(request, 'accounts/login.html')

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
def delete_file(request, file_id):
    if request.method == 'POST':
        file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
        file.file.delete()  # Delete the file from storage
        file.delete()  # Delete the database entry
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@login_required
def library_view(request):
    files = UploadedFile.objects.filter(user=request.user)
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