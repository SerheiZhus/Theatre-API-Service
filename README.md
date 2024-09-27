# Theatre API
API service for theatre management written on Django Rest Framework

## User
* email: user_1@user.com
* password: 1qazcde3

## Superuser
* email: admin@admin.ua
* password: 1qazcde3


## Installation using GitHub
* Python3 must be already installed. 
* Install Postgres and create a database.
* git clone https://github.com/SerheiZhus/Theatre-API-Service.git
* cd theatre_API_service
* python3 -m venv venv
* source venv/bin/activate
* pip install -r requirements.txt


## .env Create a .env file in the root of the project and add the following variables:
- DB_HOST=<your db hostname>
- DB_NAME=<your db name>
- DB_USER=<your db username>
- DB_PASSWORD=<your db password>
- SECRET_KEY=<your secret key>

* python manage.py migrate, python manage.py runserver

## Run with Docker
- Docker should be installed.
* docker-compose build
* docker-compose up

## Getting access
* get access to the admin panel via /admin/ using superuser credentials
* create user via /api/v1/users/registration/
* get access token via /api/users/token/
* get access token refresh via /api/users/token/refresh/
* get access to the API Root via /api/theatre/ using the access token

## Features
* JWT authentication
* Admin panel /admin/
* Documentation is located at /api/doc/swagger/
* Managing performances and tickets
* Creating plays with actors and genres
* Creating theatre halls
* Creating performances with plays and theatre halls
* Creating tickets for performances
* Filtering plays by genre, actors, and title
