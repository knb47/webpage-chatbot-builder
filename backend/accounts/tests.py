"""Tests for the deployment pipeline: models, endpoint formats, and the
Celery deploy task with AWS mocked out. Run with:

    python manage.py test backend.accounts
"""

from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase

from . import copilot
from .models import Deployment, UploadedFile
from .deployment.aws_utils import clients


def make_user(username="alice"):
    return get_user_model().objects.create_user(username=username, password="pw-12345")


def make_uploaded_file(user, name="bot.yaml", config_name="bot_1"):
    f = UploadedFile(user=user, file_name=name, chat_configuration_name=config_name)
    f.file.save(name, ContentFile(b"initialization:\n  - start_state: 'welcome'\n"), save=True)
    return f


# Minimal config that passes copilot.validate_config.
VALID_YAML = """\
bot_name: "Test"
initialization:
  - role: "assistant"
  - context: "x"
  - start_state: "start"
states:
  - state: "start"
    trigger: "t"
    goal: "g"
    states_available: ["start"]
"""


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


class CopilotTests(TestCase):
    """Config Copilot: fenced-YAML extraction and the save endpoint."""

    def _mock_claude(self, text):
        resp = mock.Mock()
        resp.json.return_value = {"content": [{"type": "text", "text": text}]}
        resp.raise_for_status = mock.Mock()
        return resp

    def test_chat_extracts_fenced_yaml(self):
        text = "Here you go!\n```yaml\n" + VALID_YAML + "```\nAnything else?"
        with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}), \
             mock.patch.object(copilot.requests, "post", return_value=self._mock_claude(text)):
            reply, yaml_text = copilot.chat([{"role": "user", "content": "make a bot"}], "")
        self.assertIn("Here you go!", reply)
        self.assertNotIn("```", reply)
        self.assertIn('bot_name: "Test"', yaml_text)

    def test_chat_without_fence_returns_no_yaml(self):
        with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}), \
             mock.patch.object(copilot.requests, "post", return_value=self._mock_claude("What audience?")):
            reply, yaml_text = copilot.chat([{"role": "user", "content": "hi"}], "")
        self.assertEqual(reply, "What audience?")
        self.assertIsNone(yaml_text)

    def test_save_endpoint_creates_uploaded_file(self):
        import json
        user = make_user("saver")
        self.client.force_login(user)
        res = self.client.post(
            "/api/accounts/copilot/save/",
            data=json.dumps({"chatbot_name": "My Bot!", "yaml": VALID_YAML}),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["file_name"], "my_bot.yaml")
        self.assertTrue(UploadedFile.objects.filter(user=user, chat_configuration_name="My Bot!").exists())

    def test_save_rejects_duplicate_name(self):
        import json
        user = make_user("saver2")
        self.client.force_login(user)
        for expected in (200, 409):
            res = self.client.post(
                "/api/accounts/copilot/save/",
                data=json.dumps({"chatbot_name": "dup", "yaml": VALID_YAML}),
                content_type="application/json",
            )
            self.assertEqual(res.status_code, expected)


class ValidatorTests(TestCase):
    """copilot.validate_config catches broken configs before users see them."""

    GOOD = """
bot_name: "T"
initialization:
  - role: "assistant"
  - context: "x"
  - start_state: "start"
states:
  - state: "start"
    trigger: "t"
    goal: "g"
    states_available: ["start", "done"]
  - state: "done"
    trigger: "t"
    goal: "g"
    states_available: ["done"]
"""

    def test_valid_config_passes(self):
        self.assertEqual(copilot.validate_config(self.GOOD), [])

    def test_unparseable_yaml_reports(self):
        errs = copilot.validate_config("states: [unclosed")
        self.assertTrue(errs and "parseable" in errs[0])

    def test_undefined_state_reference(self):
        errs = copilot.validate_config(self.GOOD.replace('"done"]', '"missing"]', 1))
        self.assertTrue(any("undefined state" in e for e in errs))

    def test_missing_start_state(self):
        errs = copilot.validate_config(self.GOOD.replace('start_state: "start"', 'start_state: "nope"'))
        self.assertTrue(any("not a defined state" in e for e in errs))

    def test_chat_retries_until_valid(self):
        bad = "Here!\n```yaml\nstates: [unclosed\n```"
        good = "Fixed!\n```yaml" + self.GOOD + "```"
        responses = [self._resp(bad), self._resp(good)]
        with mock.patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test"}), \
             mock.patch.object(copilot.requests, "post", side_effect=responses) as post:
            reply, yaml_text = copilot.chat([{"role": "user", "content": "go"}], "")
        self.assertEqual(post.call_count, 2)            # one automatic fix round
        self.assertEqual(copilot.validate_config(yaml_text), [])

    def _resp(self, text):
        r = mock.Mock()
        r.json.return_value = {"content": [{"type": "text", "text": text}]}
        r.raise_for_status = mock.Mock()
        return r


class SessionTests(TestCase):
    """Builder sessions: autosave on chat, list, restore, delete."""

    def setUp(self):
        self.user = make_user("sess")
        self.client.force_login(self.user)

    def _chat(self, body):
        import json as _json
        return self.client.post("/api/accounts/copilot/chat/",
                                data=_json.dumps(body), content_type="application/json")

    def test_chat_creates_session_and_persists_history(self):
        from .models import BuilderSession
        with mock.patch.object(copilot, "chat", return_value=("Hello!", "bot_name: x\n")):
            res = self._chat({"messages": [{"role": "user", "content": "Build me a tutor bot"}],
                              "current_yaml": ""})
        self.assertEqual(res.status_code, 200)
        sid = res.json()["session_id"]
        s = BuilderSession.objects.get(id=sid, user=self.user)
        self.assertEqual(s.title, "Build me a tutor bot")
        self.assertEqual(s.messages[-1], {"role": "assistant", "content": "Hello!"})
        self.assertEqual(s.yaml_text, "bot_name: x\n")

        # continues in the same session
        with mock.patch.object(copilot, "chat", return_value=("More.", None)):
            res2 = self._chat({"messages": s.messages + [{"role": "user", "content": "add a state"}],
                               "current_yaml": s.yaml_text, "session_id": sid})
        self.assertEqual(res2.json()["session_id"], sid)
        s.refresh_from_db()
        self.assertEqual(len(s.messages), 4)
        self.assertEqual(s.yaml_text, "bot_name: x\n")  # unchanged when no new yaml

    def test_list_restore_delete(self):
        from .models import BuilderSession
        s = BuilderSession.objects.create(user=self.user, title="My agent",
                                          messages=[{"role": "user", "content": "hi"}],
                                          yaml_text="a: 1\n")
        lst = self.client.get("/api/accounts/copilot/sessions/").json()["sessions"]
        self.assertEqual(lst[0]["title"], "My agent")
        detail = self.client.get(f"/api/accounts/copilot/sessions/{s.id}/").json()
        self.assertEqual(detail["yaml"], "a: 1\n")
        self.client.delete(f"/api/accounts/copilot/sessions/{s.id}/")
        self.assertFalse(BuilderSession.objects.filter(id=s.id).exists())

    def test_sessions_are_private(self):
        from .models import BuilderSession
        other = make_user("other")
        s = BuilderSession.objects.create(user=other, title="theirs")
        self.assertEqual(self.client.get(f"/api/accounts/copilot/sessions/{s.id}/").status_code, 404)
