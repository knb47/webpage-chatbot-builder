#!/bin/sh
echo "Running in ${DJANGO_ENV:-production} mode"

# Make migrations
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Bundle static assets
python manage.py collectstatic --noinput

if [ "$DJANGO_ENV" = "development" ]; then
    echo "Starting Django development server"
    python manage.py runserver 0.0.0.0:8000 &
else
    echo "Starting Gunicorn"
    gunicorn backend.wsgi:application --bind 0.0.0.0:8000 --timeout 120 --log-level debug &
fi

# Wait and keep the container running
wait