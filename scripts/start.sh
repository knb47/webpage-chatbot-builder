#!/bin/sh
#!/bin/sh
echo "Running in ${DJANGO_ENV:-development} mode"

# Make migrations
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Start gunicorn
gunicorn backend.wsgi:application --bind 0.0.0.0:8000 --timeout 120