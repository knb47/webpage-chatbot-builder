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
from django.db import transaction
import logging
import re, json

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
            file_name = request.POST.get('new_file_name', file.name).split('/')[-1]

            # Use a default chatbot name based on the file name and user ID
            chatbot_name = f"{file_name.rsplit('.', 1)[0]}_{request.user.id}"

            # Check if a file with the same name already exists for the user
            if UploadedFile.objects.filter(user=request.user, file_name=file_name).exists():
                return JsonResponse({'exists': True, 'file_name': file_name})

            # Save the file with the default chatbot name
            newfile = UploadedFile(
                file=file,
                file_name=file_name,
                chat_configuration_name=chatbot_name,
                user=request.user
            )
            newfile.save()

            logger.info(f"File uploaded with name: {file_name} by user: {request.user.id}, chatbot name: {chatbot_name}")

            # Return the file_id for use in renaming the chatbot
            return JsonResponse({'exists': False, 'file_id': newfile.id})

        return render(request, 'upload.html', {'form': form})

@method_decorator(login_required, name='dispatch')
class UpdateChatbotNameView(View):
    def post(self, request, file_id):
        # Parse JSON body
        try:
            data = json.loads(request.body)
            new_chatbot_name = data.get('chatbot_name', '').strip()
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid data'})

        logger.info(f"Requesting update chatbot name to: {new_chatbot_name} for file: {file_id} by user: {request.user.id}")

        # Validate the new chatbot name
        if not new_chatbot_name or not self.is_valid_name(new_chatbot_name):
            return JsonResponse({'success': False, 'error': 'Invalid chatbot name'})

        uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)

        # Check for name conflicts
        if UploadedFile.objects.filter(user=request.user, chat_configuration_name=new_chatbot_name).exclude(id=file_id).exists():
            return JsonResponse({'success': False, 'error': 'Chatbot name already exists'})

        # Update the chatbot name
        uploaded_file.chat_configuration_name = new_chatbot_name
        uploaded_file.save()

        logger.info(f"Chatbot name updated to: {new_chatbot_name} for file: {uploaded_file.file_name} by user: {request.user.id}")

        return JsonResponse({'success': True})

    def is_valid_name(self, name):
        """Validate the chatbot name for allowed characters."""
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))


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
def builder_view(request):
    # copilot is imported at the bottom of this module; resolved at call time.
    return render(request, 'builder.html', {'starter_yaml': copilot.STARTER_YAML})

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
        try:
            with transaction.atomic():
              deployment = get_object_or_404(Deployment, id=deployment_id, user=request.user)
              deployment.config_file.has_deployment = False
              deployment.config_file.save(update_fields=['has_deployment'])
              deployment.delete()
              return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f'Error deleting deployment {deployment_id}: {e}')
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
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

# --------------------------------------------------------------------------
# Config copilot (the builder page): chat with Claude to write the config,
# then save the YAML as an UploadedFile ready for deployment.
# --------------------------------------------------------------------------

from django.core.files.base import ContentFile
from django.views.decorators.http import require_POST
from .. import copilot


@login_required
@require_POST
def copilot_chat_view(request):
    try:
        data = json.loads(request.body)
        reply, yaml_text = copilot.chat(
            data.get('messages', []),
            data.get('current_yaml', ''),
        )
        return JsonResponse({'reply': reply, 'yaml': yaml_text})
    except Exception as e:
        logger.error(f"Copilot chat failed: {e}")
        return JsonResponse({'error': str(e)}, status=502)


@login_required
@require_POST
def copilot_save_view(request):
    try:
        data = json.loads(request.body)
        name = (data.get('chatbot_name') or '').strip()
        yaml_text = data.get('yaml') or ''
        if not name or not yaml_text:
            return JsonResponse({'error': 'chatbot_name and yaml are required'}, status=400)

        file_name = re.sub(r'[^A-Za-z0-9_-]+', '_', name).strip('_').lower() + '.yaml'
        if UploadedFile.objects.filter(user=request.user, chat_configuration_name=name).exists():
            return JsonResponse({'error': f'A config named "{name}" already exists.'}, status=409)

        uploaded = UploadedFile(user=request.user, file_name=file_name, chat_configuration_name=name)
        uploaded.file.save(file_name, ContentFile(yaml_text.encode('utf-8')), save=True)
        return JsonResponse({'file_id': uploaded.id, 'file_name': file_name})
    except Exception as e:
        logger.error(f"Copilot save failed: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def copilot_starter_yaml():
    return copilot.STARTER_YAML
