# Use the official Python 3.11 image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy Poetry configuration files first for better caching
COPY pyproject.toml poetry.lock* /app/

# Install project dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the project files
COPY . /app/

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