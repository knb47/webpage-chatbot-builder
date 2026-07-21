# Define commands
BUILD_REACT_DEV=npx webpack --mode development
BUILD_REACT_PROD=npx webpack --mode production
BUILD_OTHER_STATIC=poetry run python manage.py collectstatic --noinput
PORT=8000
DJANGO_SERVER=poetry run python manage.py runserver $(PORT)

# Clean old builds
clean:
	rm -rf backend/static/js/bundle.js
	rm -rf backend/staticfiles/*

# Install dependencies
check-deps:
	poetry install
	npm install

# Run migrations
migrations:
	poetry run python manage.py makemigrations
	poetry run python manage.py migrate

# Bundle All static files for development
bundle-dev:
	$(BUILD_REACT_DEV)
	$(BUILD_OTHER_STATIC)

# Bundle All static files for production
bundle-prod:
	$(BUILD_REACT_PROD)
	$(BUILD_OTHER_STATIC)

# Watch mode for development
watch:
	npx webpack --mode development --watch

# Run Django server
server:
	$(DJANGO_SERVER)

# Combined target to bundle and run the server for development
dev: clean check-deps migrations bundle-dev server

# Combined target to bundle and run the server for production
prod: clean check-deps migrations bundle-prod

# ---------------------------------------------------------------------------
# Full-stack local demo: LocalStack ("AWS") + Terraform + control plane.
# Prereqs: Docker; .env.demo (copy .env.demo.example and fill in).
# ---------------------------------------------------------------------------

# 1. Start LocalStack and provision base infra (IAM role, API GW, S3).
demo-infra:
	docker compose -f infra/localstack/docker-compose.yml up -d
	docker run --rm --network localstack_default \
		-v $(CURDIR)/infra/terraform:/tf -w /tf \
		hashicorp/terraform:1.9 init -input=false
	docker run --rm --network localstack_default \
		-v $(CURDIR)/infra/terraform:/tf -w /tf \
		hashicorp/terraform:1.9 apply -auto-approve -var aws_endpoint=http://localstack:4566

# 2. Build the engine deployment package from source.
demo-package:
	bash backend/accounts/deployment/pull_package.sh

# 3. Bring up the control plane (Django + Celery + RabbitMQ + Postgres).
demo-up:
	docker compose -f docker-compose.demo.yml up --build -d
	@echo "Control plane: http://localhost:8000  (LocalStack edge: http://localhost:4566)"

demo-down:
	docker compose -f docker-compose.demo.yml down
	docker compose -f infra/localstack/docker-compose.yml down

.PHONY: clean check-deps migrations bundle-dev bundle-prod watch server dev prod \
	demo-infra demo-package demo-up demo-down