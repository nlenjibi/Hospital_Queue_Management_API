# Hospital Queue Management API

A Django RESTful API for managing hospital queues, users, staff, patients, notifications, and labs. This project supports JWT authentication, role-based permissions, and real-time notifications via WebSockets.

## Features

- User registration, authentication, and role management (admin, doctor, nurse, patient, staff, superadmin)
- Patient profile and queue management
- Department and staff management
- Lab and notification modules
- JWT authentication for secure API access
- WebSocket support for real-time notifications
- Throttling and permissions for sensitive endpoints
- Admin interface for all models
- Automated tests for models and APIs

## Tech Stack

- Python 3.11+
- Django 5.1+
- Django REST Framework
- Django Channels (WebSocket)
- JWT Authentication (djangorestframework-simplejwt)
- SQLite (default, can be swapped for PostgreSQL)

## Setup

1. **Clone the repository:**
   ```powershell
   git clone <your-repo-url>
   cd Hospital_Queue_Management_API
   ```
2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
4. **Apply migrations:**
   ```powershell
   py manage.py migrate
   ```
5. **Create a superuser (for admin access):**
   ```powershell
   py manage.py createsuperuser
   ```
6. **Run the development server:**
   ```powershell
   py manage.py runserver
   ```

## API Endpoints

See `users/urls.py`, `hospital/urls.py`, `queues/urls.py`, `labs/urls.py`, and `notifications/urls.py` for all endpoints.

Example endpoints:

- `/api/register/` - Register a new user
- `/api/login/` - Obtain JWT token
- `/api/users/` - List users (admin only)
- `/api/patients/` - List patients
- `/api/queues/` - Manage queues
- `/api/labs/` - Lab operations
- `/api/notifications/` - Notification management

## Authentication

All sensitive endpoints require JWT authentication. Include your token in the header:

```
Authorization: Bearer <your_token>
```

## Testing

Run all tests:

```powershell
py manage.py test
```

## Documentation

- API usage examples are provided in the `*.api.example.usage.json` files.
- You can generate HTML docs from Markdown using the `markdown` Python package or use MkDocs for a full documentation site.

## Postman

- Import the provided API example JSON files into Postman for testing.

## Contributing

Pull requests are welcome! Please add tests for new features and follow PEP8 style.

## License

MIT

---

For questions or support, contact the project maintainer.
