# Use an official Python runtime as a parent image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y netcat-openbsd

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock* /app/

# Install project dependencies
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# Copy project
COPY . /app/

# Copy the start script
COPY scripts/start.sh /app/scripts/start.sh

# Make the start script executable
RUN chmod +x /app/scripts/start.sh

# Run the start script
CMD ["/app/scripts/start.sh"]