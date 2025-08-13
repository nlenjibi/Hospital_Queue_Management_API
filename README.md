# Hospital Queue Management API

A Django REST API for managing hospital queues, users, and authentication.

## Features

- Custom user model with roles (admin, doctor, nurse, patient)
- JWT authentication (login, registration)
- Argon2 password hashing
- Rate limiting for authentication endpoints
- Modular apps for users and hospital management

## Setup

1. **Clone the repository**
2. **Install dependencies**
   - `pip install -r requirements.txt`
3. **Apply migrations**
   - `python manage.py migrate`
4. **Run the server**
   - `python manage.py runserver`

## API Endpoints

- `POST /api/auth/register/` — Register a new user
- `POST /api/auth/login/` — Obtain JWT tokens

## Security

- Passwords hashed with Argon2
- Rate limiting on login and registration endpoints

## Development

- Python 3.11+
- Django 5.1+
- DRF, SimpleJWT, Argon2, django-ratelimit

## License

MIT
