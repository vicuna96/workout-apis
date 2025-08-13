# Workout Tracker REST API Documentation

## Overview

The Workout Tracker REST API provides comprehensive endpoints for managing user workouts, authentication, and analytics. Built with Flask, SQLAlchemy, and JWT authentication.

## Base URL
```
http://localhost:5000/api
```

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## API Endpoints

### Authentication

#### Register User
```http
POST /auth/register
```

**Request Body:**
```json
{
    "username": "string (min 3 chars)",
    "email": "string (valid email)",
    "password": "string (min 6 chars)"
}
```

**Response (201):**
```json
{
    "message": "User registered successfully",
    "access_token": "jwt_token_here",
    "user": {
        "id": 1,
        "username": "fitguy123",
        "email": "fitguy@example.com",
        "created_at": "2025-08-12T10:00:00"
    }
}
```

#### Login
```http
POST /auth/login
```

**Request Body:**
```json
{
    "username": "string (username or email)",
    "password": "string"
}
```

**Response (200):**
```json
{
    "message": "Login successful",
    "access_token": "jwt_token_here",
    "user": {
        "id": 1,
        "username": "fitguy123",
        "email": "fitguy@example.com",
        "created_at": "2025-08-12T10:00:00"
    }
}
```

#### Get Current User
```http
GET /auth/me
```
*Requires authentication*

**Response (200):**
```json
{
    "user": {
        "id": 1,
        "username": "fitguy123",
        "email": "fitguy@example.com",
        "created_at": "2025-08-12T10:00:00"
    }
}
```

### Workouts

#### Create Workout Set
```http
POST /workouts
```
*Requires authentication*

**Request Body:**
```json
{
    "exercise": "Bench Press",
    "weight": 135.5,
    "reps": 10,
    "workout_date": "2025-08-12"
}
```

**Response (201):**
```json
{
    "message": "Workout set created successfully",
    "workout_set": {
        "id": 1,
        "exercise": "Bench Press",
        "weight": 135.5,
        "reps": 10,
        "workout_date": "2025-08-12",
        "created_at": "2025-08-12T10:00:00",
        "volume": 1355.0
    }
}
```

#### Get Workout Sets
```http
GET /workouts
```
*Requires authentication*

**Query Parameters:**
- `date` - Filter by specific date (YYYY-MM-DD)
- `date_from` - Filter from date (YYYY-MM-DD)
- `date_to` - Filter to date (YYYY-MM-DD)
- `exercise` - Filter by exercise name (partial match)

**Examples:**
```http
GET /workouts?date=2025-08-12
GET /workouts?exercise=Bench Press
GET /workouts?date_from=2025-08-01&date_to=2025-08-15
```

**Response (200):**
```json
{
    "workout_sets": [
        {
            "id": 1,
            "exercise": "Bench Press",
            "weight": 135.5,
            "reps": 10,
            "workout_date": "2025-08-12",
            "created_at": "2025-08-12T10:00:00",
            "volume": 1355.0
        }
    ],
    "total": 1
}
```

#### Get Specific Workout Set
```http
GET /workouts/{id}
```
*Requires authentication*

**Response (200):**
```json
{
    "workout_set": {
        "id": 1,
        "exercise": "Bench Press",
        "weight": 135.5,
        "reps": 10,
        "workout_date": "2025-08-12",
        "created_at": "2025-08-12T10:00:00",
        "volume": 1355.0
    }
}
```

#### Update Workout Set
```http
PUT /workouts/{id}
```
*Requires authentication*

**Request Body:**
```json
{
    "exercise": "Bench Press",
    "weight": 140.0,
    "reps": 8,
    "workout_date": "2025-08-12"
}
```

**Response (200):**
```json
{
    "message": "Workout set updated successfully",
    "workout_set": {
        "id": 1,
        "exercise": "Bench Press",
        "weight": 140.0,
        "reps": 8,
        "workout_date": "2025-08-12",
        "created_at": "2025-08-12T10:00:00",
        "volume": 1120.0
    }
}
```

#### Delete Workout Set
```http
DELETE /workouts/{id}
```
*Requires authentication*

**Response (200):**
```json
{
    "message": "Workout set deleted successfully"
}
```

#### Duplicate Workout Set
```http
POST /workouts/{id}/duplicate
```
*Requires authentication*

**Request Body (optional):**
```json
{
    "workout_date": "2025-08-13"
}
```

**Response (201):**
```json
{
    "message": "Workout set duplicated successfully",
    "workout_set": {
        "id": 2,
        "exercise": "Bench Press",
        "weight": 135.5,
        "reps": 10,
        "workout_date": "2025-08-13",
        "created_at": "2025-08-12T10:00:00",
        "volume": 1355.0
    }
}
```

### Analytics

#### Get Exercise List
```http
GET /analytics/exercises
```
*Requires authentication*

**Response (200):**
```json
{
    "exercises": [
        "Bench Press",
        "Deadlift",
        "Squat"
    ]
}
```

#### Get Exercise Progress
```http
GET /analytics/progress/{exercise_name}
```
*Requires authentication*

**Response (200):**
```json
{
    "exercise": "Bench Press",
    "progress_data": [
        {
            "date": "2025-08-10",
            "max_weight": 175.0,
            "avg_weight": 155.0,
            "total_volume": 4650.0,
            "sets": 3
        },
        {
            "date": "2025-08-12",
            "max_weight": 180.0,
            "avg_weight": 160.0,
            "total_volume": 4800.0,
            "sets": 3
        }
    ],
    "total_workouts": 2,
    "total_sets": 6
}
```

#### Get Workout Summary
```http
GET /analytics/summary
```
*Requires authentication*

**Query Parameters:**
- `date_from` - From date (YYYY-MM-DD)
- `date_to` - To date (YYYY-MM-DD)

**Response (200):**
```json
{
    "total_sets": 25,
    "total_volume": 15750.0,
    "workout_days": 8,
    "exercises": 5,
    "date_range": {
        "from": "2025-08-01",
        "to": "2025-08-15"
    }
}
```

### Health Check

#### Health Status
```http
GET /health
```

**Response (200):**
```json
{
    "status": "healthy",
    "timestamp": "2025-08-12T10:00:00",
    "version": "1.0.0"
}
```

## Error Responses

All error responses follow this format:

```json
{
    "error": "Error Type",
    "message": "Detailed error message"
}
```

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (authentication required)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

## Setup and Installation

### Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set environment variables:**
```bash
export SECRET_KEY="your-secret-key"
export JWT_SECRET_KEY="your-jwt-secret"
export DATABASE_URL="sqlite:///workout_tracker.db"
```

3. **Run the application:**
```bash
python workout_api.py
```

### Docker Deployment

1. **Build and run with Docker Compose:**
```bash
docker-compose up --build
```

This will start:
- PostgreSQL database
- Flask API server
- Nginx reverse proxy

### Environment Variables

- `SECRET_KEY` - Flask secret key for sessions
- `JWT_SECRET_KEY` - JWT signing secret
- `DATABASE_URL` - Database connection string
- `FLASK_ENV` - Environment (development/production)

## Rate Limiting

API requests are rate-limited to 10 requests per second per IP address when using the Nginx configuration.

## Security Features

- Password hashing using Werkzeug
- JWT token authentication
- Input validation and sanitization
- SQL injection protection via SQLAlchemy ORM
- CORS headers configured
- Security headers (XSS protection, content type options, etc.)

## Database Schema

### Users Table
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email address
- `password_hash` - Hashed password
- `created_at` - Registration timestamp

### Workout Sets Table
- `id` - Primary key
- `user_id` - Foreign key to users table
- `exercise` - Exercise name
- `weight` - Weight lifted
- `reps` - Number of repetitions
- `workout_date` - Date of workout
- `created_at` - Creation timestamp

## Integration with Frontend

The API is designed to work seamlessly with the React frontend application. Here's how to update the frontend to use the API:

1. **Replace localStorage with API calls**
2. **Add authentication flow**
3. **Update data fetching to use HTTP requests**
4. **Handle loading states and errors**

Example frontend integration:

```javascript
// API client for the workout tracker
class WorkoutAPI {
    constructor(baseURL = 'http://localhost:5000/api') {
        this.baseURL = baseURL;
        this.token = localStorage.getItem('token');
    }

    async login(username, password) {
        const response = await fetch(`${this.baseURL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            this.token = data.access_token;
            localStorage.setItem('token', this.token);
            return data;
        }
        throw new Error('Login failed');
    }

    async getWorkouts(filters = {}) {
        const params = new URLSearchParams(filters);
        const response = await fetch(`${this.baseURL}/workouts?${params}`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });
        
        if (response.ok) {
            return await response.json();
        }
        throw new Error('Failed to fetch workouts');
    }

    async addWorkoutSet(exercise, weight, reps, workoutDate) {
        const response = await fetch(`${this.baseURL}/workouts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            },
            body: JSON.stringify({
                exercise,
                weight,
                reps,
                workout_date: workoutDate
            })
        });
        
        if (response.ok) {
            return await response.json();
        }
        throw new Error('Failed to add workout set');
    }
}
```

This API provides a robust backend for the workout tracking application with proper authentication, data validation, and analytics capabilities.