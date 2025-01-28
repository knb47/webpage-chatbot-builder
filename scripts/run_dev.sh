poetry run python manage.py makemigrations
poetry run python manage.py migrate
poetry run python manage.py collectstatic --noinput
npm build
poetry run python manage.py runserver