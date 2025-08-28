# Hospital Queue Management API Documentation

## Authentication

All sensitive endpoints require JWT authentication. Include your token in the header:

```
Authorization: Bearer <your_token>
```

## Endpoints

### User Registration

- **POST** `/api/register/`
- **Request:**

```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "newpass123",
  "password_confirm": "newpass123",
  "role": "patient"
}
```

- **Response:**

```json
{
  "user": { ... },
  "access": "<jwt_token>",
  "refresh": "<refresh_token>"
}
```

### User Login

- **POST** `/api/login/`
- **Request:**

```json
{
  "email": "newuser@example.com",
  "password": "newpass123"
}
```

- **Response:**

```json
{
  "user": { ... },
  "access": "<jwt_token>",
  "refresh": "<refresh_token>"
}
```

### List Users

- **GET** `/api/users/` (Admin only)
- **Response:**

```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin"
  }
]
```

### Patient Profile

- **GET** `/api/profile/patient/` (Authenticated patient)
- **Response:**

```json
{
  "id": 1,
  "user": {
    "id": 2,
    "username": "pat",
    "email": "pat@example.com",
    "role": "patient"
  },
  "medical_id": "MED000001",
  "priority_level": "walk_in",
  "date_of_birth": "1990-01-01",
  "emergency_contact": "",
  "address": "",
  "allergies": "",
  "notes": ""
}
```

### List Patients

- **GET** `/api/patients/` (Admin only)
- **Response:**

```json
[
  {
    "id": 1,
    "user": { ... },
    "medical_id": "MED000001",
    "priority_level": "walk_in"
  }
]
```

### Queue Management

- **GET** `/api/queues/` (Admin only)
- **POST** `/api/queues/` (Admin only)
- **GET** `/api/queues/{id}/` (Authenticated)

### Department Management

- **GET** `/api/departments/` (Admin only)
- **POST** `/api/departments/` (Admin only)
- **GET** `/api/departments/{id}/` (Authenticated)

### Staff Management

- **GET** `/api/staff/` (Admin only)
- **POST** `/api/staff/` (Admin only)
- **GET** `/api/staff/{id}/` (Authenticated)

### Lab Management

- **GET** `/api/labs/` (Admin only)
- **POST** `/api/labs/` (Admin only)
- **GET** `/api/labs/{id}/` (Authenticated)

### Notifications

- **GET** `/api/notifications/` (Authenticated)
- **POST** `/api/notifications/` (Admin only)

## Models

### User

- `username` (string, required)
- `email` (string, required)
- `role` (choice: admin, doctor, nurse, patient, staff, superadmin)
- `phone_number` (string, optional)
- `created_at` (datetime)
- `updated_at` (datetime)

### Patient

- `user` (User, required)
- `medical_id` (string, required)
- `priority_level` (choice: emergency, appointment, walk_in)
- `date_of_birth` (date, optional)
- `emergency_contact` (string, optional)
- `address` (string, optional)
- `allergies` (string, optional)
- `notes` (string, optional)

### Staff

- `user` (User, required)
- `department` (Department, required)
- `role` (choice: doctor, nurse, staff)
- `specialty` (string, optional)
- `license_number` (string, optional)
- `shift_start` (time)
- `shift_end` (time)

### Department

- `name` (string, required)
- `department_type` (choice: OPD, LAB, PHARMACY, ER)
- `description` (string, optional)
- `is_active` (boolean)

### Queue

- `department` (Department, required)
- `name` (string, required)
- `is_active` (boolean)
- `max_capacity` (integer)
- `avg_processing_time` (integer)

## Error Codes

- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Insufficient permissions
- `400 Bad Request`: Validation errors
- `429 Too Many Requests`: Throttling limit reached

## Permissions

- Only admins can list all users, patients, staff, departments, queues, and labs.
- Patients can view their own profile.
- Authenticated users can view details of their own records.

## Example Usage

See the `*.api.example.usage.json` files for request/response samples.

## Postman

Import the provided API example JSON files into Postman for testing.

---

For more details, see the code and README.
