# Use the official Python 3.11 image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Optional: corporate root CAs for machines behind a TLS-inspecting proxy.
# The glob is paired with an always-present file so COPY stays valid when the
# CA bundle is absent. All later downloads (apt, curl, pip/poetry, npm) then
# trust the proxy.
COPY pyproject.toml corp-ca-bundle.pem* /tmp/ca/
RUN if [ -f /tmp/ca/corp-ca-bundle.pem ]; then \
      cp /tmp/ca/corp-ca-bundle.pem /usr/local/share/ca-certificates/corp-ca.crt && \
      update-ca-certificates; \
    fi
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt \
    PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org pypi.python.org"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy Poetry configuration files first for better caching
COPY pyproject.toml poetry.lock* /app/

# Install project dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the project files
COPY . /app/

# Install npm dependencies and build React assets
RUN cd /app && npm install && npx webpack --mode production

# Create and switch to a non-root user
RUN adduser --disabled-password --gecos '' myuser

# Set permissions for the staticfiles directory
RUN mkdir -p /app/backend/staticfiles && \
    chown -R myuser:myuser /app/backend/staticfiles && \
    chmod -R 755 /app/backend/staticfiles

# Switch to the new user
USER myuser

# Run collectstatic command as a non-root user
RUN python manage.py collectstatic --noinput

# Switch back to root user to set script permissions
USER root
RUN chmod +x /app/scripts/_start.sh

# Run the start script
CMD ["/app/scripts/_start.sh"]