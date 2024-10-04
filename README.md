# This application is a work in progress

Project purpose: To allow business to create custom chat agents and deploy them on their webpages to handle user queries.
Inspiration: Most chat agents on websites don't allow users to perform actions such as buy a product or cancel an appointment.

Solution: Create a no-code solution that allows business to deploy chat agents to their webpages.

How: Create a chat engine that handles conversational flow in a standardized manner. Then enable business to build a states and actions to feed into the chat engine.

Technologies: AWS, Django, FastAPI, LangChain

ui-local: poetry run python manage.py runserver

prod-prod: docker-compose -f docker-compose.prod.yml up --build

poetry run python manage.py collectstatic


# Application Setup and Deployment Guide

This guide will help you set up and run the application in development and production environments using Docker and Docker Compose.

## Prerequisites

- Docker
- Docker Compose
- Poetry
- Python 3.x (for UI development)

## Running the Application

To run the UI locally in development mode:
docker-compose-f docker-compose.dev.yml 

To run the server in production mode:
docker-compose -f docker-compose.prod.yml up --build

# Application Overview

![Alt text](./README.md)