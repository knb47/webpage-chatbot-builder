# backend/settings/demo.py
#
# Full-stack local demo: real deploy pipeline (DJANGO_ENV=production selects
# the prod views/tasks) with AWS emulated by LocalStack — Postgres stands in
# for RDS, uploads go to S3 (LocalStack), tenant Lambdas run in LocalStack.
#
# DEBUG stays on so Django serves its own static files; this settings module
# is for the local demo stack only, never a public deployment.

import os

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'web']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'chapp'),
        'USER': os.environ.get('DB_USER', 'chapp'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'chapp'),
        'HOST': os.environ.get('DB_HOST', 'postgres'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Uploaded tenant configs -> S3 (LocalStack edge, path-style addressing).
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'test')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', 'test')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'chapp-tenant-configs')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_ENDPOINT_URL', 'http://localstack:4566')
AWS_S3_ADDRESSING_STYLE = 'path'
AWS_DEFAULT_ACL = None
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS + [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
