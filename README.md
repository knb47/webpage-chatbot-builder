# Chapp — No-Code AI Agent Builder

A no-code platform for creating custom AI chat agents. Users describe the
agent they want to a **Config Copilot** (chat on the left, live YAML on the
right), save it under a name, and deploy an isolated, working assistant —
without writing backend code.

This repo is the **control plane and UI**: auth, the Config Copilot builder,
and deployment management (Django). Every assistant built here is powered by
the **[chapp-engine](https://github.com/knb47/chapp-engine)** (FastAPI +
LangChain + Claude), which this app packages with the user's config and
provisions per tenant.

```
        this repo (control plane)                     AWS (or LocalStack)
┌──────────────────────────────────────┐      ┌────────────────────────────────┐
│  Django + DRF       Config Copilot   │      │  API Gateway (shared)          │
│  auth · uploads · deployments UI     │      │    /user/{id}/agent/{v}/{bot}  │
│           │                          │      │        │                       │
│           ▼                          │      │        ▼                       │
│  RabbitMQ ──► Celery worker ── boto3 ┼─────►│  Lambda (per tenant)           │
│                   │                  │      │   └─ chat engine + config      │
│  Postgres         └─ engine zip      │      │  S3 (tenant configs)           │
│  (users, deployments)                │      └────────────────────────────────┘
└──────────────────────────────────────┘
```

## What happens on "Deploy"

1. The Config Copilot (Claude) turns a conversation into the engine's YAML
   state-machine format; the user watches and edits the config live.
2. On save, the config uploads to S3; deploying queues a Celery task.
3. The worker packages the [engine](https://github.com/knb47/chapp-skeleton)
   with the tenant's config, then provisions an **isolated Lambda** and wires
   it into a shared **API Gateway** under the tenant's route.
4. The user gets back a working chat URL — a full ChatGPT-style page with a
   live progress rail, served by their own Lambda, powered by Claude.

Teardown is first-class: deployments are tracked in Postgres and
can be deleted per tenant (`teardown_lambda.py`).

## Run the full demo locally (no AWS account)

The entire pipeline runs against **LocalStack**, provisioned by **Terraform** —
the same `.tf` files target real AWS by setting `-var aws_endpoint=""`.

```bash
# 0. prerequisites: Docker. Copy .env.demo.example -> .env.demo,
#    add your ANTHROPIC_API_KEY.

make demo-infra     # LocalStack up + terraform apply (IAM, API GW, S3)
                    #   -> put `terraform output api_gateway_id` in .env.demo
make demo-package   # build the engine Lambda zip from source (Dockerized)
make demo-up        # Django + Celery + RabbitMQ + Postgres

# then: http://localhost:8000 — register, chat with the copilot, deploy, chat.
```

Cloud mapping for the local stack: web/celery containers ↔ ECS services,
Postgres ↔ RDS, RabbitMQ ↔ Amazon MQ, LocalStack ↔ Lambda / API Gateway / S3.

## Repository layout

```
backend/
  accounts/            users, uploads, deployments (models, DRF views, tasks)
    copilot.py         Config Copilot: Claude-backed config authoring
    tasks.py           Celery: deploy_chat_app / teardown_chat_app
    deployment/
      pull_package.sh  builds the engine zip from the engine repo
      aws_utils/       boto3 provisioning: deploy / teardown,
                       clients.py (LocalStack/AWS switch via AWS_ENDPOINT_URL)
  settings/            base / development / demo / production
  ui/vanilla/          server-rendered pages: builder (copilot + YAML editor),
                       agents (deploy / teardown lifecycle)
infra/
  localstack/          pinned LocalStack compose (community image)
  terraform/           base infra: IAM role, shared API GW, S3 bucket
docker-compose.demo.yml  full local stack
```

## Development

- **Backend:** `poetry install`, then `python manage.py runserver` (uses
  `settings/development.py`: SQLite + mock deploy views, no AWS needed).
- **Real vs mock:** `DJANGO_ENV=production` selects the real views/tasks;
  anything else uses `views/mock_views.py` for offline UI work.

## Tests

```bash
poetry run python manage.py test backend.accounts
```

Covers the deployment models, the Celery deploy task against mocked AWS
clients, and the LocalStack/AWS endpoint formatting.

## Tech stack

Python · Django + DRF · Celery + RabbitMQ · PostgreSQL · boto3 ·
Terraform + LocalStack · AWS Lambda / API Gateway / S3 · Docker —
LLM: Claude (Config Copilot here; LangChain agent runtime in the
[engine repo](https://github.com/knb47/chapp-skeleton))
