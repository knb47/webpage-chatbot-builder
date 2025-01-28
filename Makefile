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

.PHONY: clean check-deps migrations bundle-dev bundle-prod watch server dev prod