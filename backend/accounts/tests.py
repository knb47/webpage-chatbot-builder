"""Tests for the deployment pipeline: models, endpoint formats, and the
Celery deploy task with AWS mocked out. Run with:

    python manage.py test backend.accounts
"""

from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase

from .models import Deployment, UploadedFile
from .deployment.aws_utils import clients


def make_user(username="alice"):
    return get_user_model().objects.create_user(username=username, password="pw-12345")


def make_uploaded_file(user, name="bot.yaml", config_name="bot_1"):
    f = UploadedFile(user=user, file_name=name, chat_configuration_name=config_name)
    f.file.save(name, ContentFile(b"initialization:\n  - start_state: 'welcome'\n"), save=True)
    return f


class ModelTests(TestCase):
    def test_config_name_unique_per_user(self):
        user = make_user()
        make_uploaded_file(user)
        with self.assertRaises(Exception):
            make_uploaded_file(user, name="other.yaml", config_name="bot_1")

    def test_deployment_links_config_and_tracks_status(self):
        user = make_user()
        uploaded = make_uploaded_file(user)
        dep = Deployment.objects.create(
            user=user, config_file=uploaded, chatbot_name="bot_1",
            config_file_path=uploaded.file.name, config_file_name=uploaded.file_name,
            endpoint="http://example.com/user/1/agent/v0/bot_1/", status="active",
        )
        self.assertEqual(uploaded.deployments.count(), 1)
        self.assertEqual(dep.status, "active")


class InvokeUrlTests(TestCase):
    """clients.invoke_url must emit the AWS or LocalStack URL format."""

    def test_aws_format_when_no_endpoint(self):
        with mock.patch.object(clients, "AWS_PUBLIC_ENDPOINT_URL", None):
            url = clients.invoke_url("abc123", "us-east-1", "prod", "user/1/agent/v0/bot/")
        self.assertEqual(
            url, "https://abc123.execute-api.us-east-1.amazonaws.com/prod/user/1/agent/v0/bot/")

    def test_localstack_format_when_endpoint_set(self):
        with mock.patch.object(clients, "AWS_PUBLIC_ENDPOINT_URL", "http://localhost:4566"):
            url = clients.invoke_url("abc123", "us-east-1", "prod", "/user/1/agent/v0/bot/")
        self.assertEqual(
            url, "http://localhost:4566/restapis/abc123/prod/_user_request_/user/1/agent/v0/bot/")


class DeployTaskTests(TestCase):
    """deploy_chat_app guards and DB effects, with AWS provisioning mocked."""

    def setUp(self):
        self.user = make_user()
        self.uploaded = make_uploaded_file(self.user)

    def _run(self, result):
        from . import tasks
        with mock.patch.object(tasks, "deploy_user_app", return_value=result):
            return tasks.deploy_chat_app(self.user.id, self.uploaded.file.name)

    def test_successful_deploy_creates_deployment_and_marks_file(self):
        result = self._run({
            "status": "completed",
            "resource_name": "user_1_agent_v0_bot_1",
            "endpoint": "http://localhost:4566/restapis/x/prod/_user_request_/user/1/agent/v0/bot_1/",
            "chatbot_name": "bot_1",
        })
        self.assertEqual(result["status"], "completed")
        self.uploaded.refresh_from_db()
        self.assertTrue(self.uploaded.has_deployment)
        dep = Deployment.objects.get(user=self.user)
        self.assertEqual(dep.resource_name, "user_1_agent_v0_bot_1")
        self.assertEqual(dep.status, "active")

    def test_already_deployed_file_is_rejected(self):
        self.uploaded.has_deployment = True
        self.uploaded.save(update_fields=["has_deployment"])
        result = self._run({"status": "completed"})
        self.assertEqual(result["status"], "failed")
        self.assertIn("already been deployed", result["error"])

    def test_duplicate_bot_name_is_rejected(self):
        Deployment.objects.create(
            user=self.user, chatbot_name=self.uploaded.chat_configuration_name,
            config_file_path="x", config_file_name="x",
            endpoint="http://example.com/", status="active",
        )
        result = self._run({"status": "completed"})
        self.assertEqual(result["status"], "failed")

    def test_failed_provisioning_creates_no_deployment(self):
        result = self._run({"status": "failed", "error": "boom"})
        self.assertEqual(result["status"], "failed")
        self.assertEqual(Deployment.objects.count(), 0)
        self.uploaded.refresh_from_db()
        self.assertFalse(self.uploaded.has_deployment)
