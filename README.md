ui-local: poetry run python manage.py runserver

prod-prod: docker-compose -f docker-compose.prod.yml up --build

poetry run python manage.py collectstatic