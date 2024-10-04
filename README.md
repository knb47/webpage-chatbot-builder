# Chatbot Builder for Webpages
## This application is currently under development.

**Project purpose:** To allow business to create custom chat agents and deploy them on their webpages to handle user queries.
Inspiration: Most chat agents on websites don't allow users to perform actions such as buy a product or cancel an appointment.

**Solution:** Create a no-code solution that allows business to deploy chat agents to their webpages.

**How:** Create a chat engine that handles conversational flow in a standardized manner. Then enable business to build a states and actions to feed into the chat engine.

**Technologies:** AWS, Django, FastAPI, LangChain

# Application Setup and Deployment Guide

This guide will help you set up and run the application in development and production environments using Docker and Docker Compose.

## Prerequisites

- Docker
- Docker Compose
- Poetry
- Python 3.x (for UI development)

## Running the Application

Add a .env.dev file to the root directory, using .env.dev.example as an example.

Add a .env.prod file to the root directory, using .env.prod.example as an example.

To run the UI locally in development mode:
docker-compose-f docker-compose.dev.yml up --build

To run the server in production mode:
docker-compose -f docker-compose.prod.yml up --build

# Application Overview

![Image of application overview.](./application_overview.md)