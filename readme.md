# FastAPI Workout Tracker

A modern, high-performance REST API for tracking workouts, built with FastAPI. Perfect for web applications, mobile apps, and fitness platforms.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://sqlalchemy.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

## ✨ Features

### 🔐 Authentication & Security
- JWT token-based authentication
- Secure password hashing (bcrypt)
- Email validation
- Rate limiting and security headers
- CORS support for web applications

### 🏋️ Workout Management
- Create, read, update, and delete workout sets
- Track exercise name, weight, reps, and date
- Automatic volume calculation (weight × reps)
- Duplicate workouts for easy logging
- Advanced filtering and search

### 📊 Analytics & Progress Tracking
- Exercise progress over time
- Workout summaries and statistics
- Volume tracking and trends
- Personal records and achievements
- Comprehensive reporting

### 🚀 Performance & Scalability
- Async/await support for high concurrency
- Database connection pooling
- Optimized queries with SQLAlchemy
- Redis caching support
- Docker containerization

### 📱 Mobile & Web Ready
- RESTful API design
- OpenAPI/Swagger documentation
- CORS configured for web apps
- Mobile app friendly endpoints
- Comprehensive error handling

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/fastapi-workout-tracker.git
cd fastapi-workout-tracker

# Run the setup script
python setup.py dev

# Start the development server
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Option 2: Docker Setup

```bash
# Clone and setup with Docker
git clone https://github.com/yourusername/fastapi-workout-tracker.git
cd fastapi-workout-tracker

# Build and run with Docker Compose
docker-compose up --build
```

Services will be available at:
- **API**: http://localhost:8000
- **Database**: PostgreSQL on port 5432
- **Cache**: Redis on port 6379
- **Web**: Nginx proxy on port 80

### Option 3: Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env file with your configuration

# Initialize database
python -c "from main import Base, engine; Base.metadata.create_all(bind=engine)"

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📖 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
    "username": "fitguy123",
    "email": "fitguy@example.com",
    "password": "password123"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
    "username": "fitguy123",
    "password": "password123"
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <your_token>
```

### Workout Endpoints

#### Add Workout Set
```http
POST /api/workouts
Authorization: Bearer <your_token>
Content-Type: application/json

{
    "exercise": "Bench Press",
    "weight": 135.5,
    "reps": 10,
    "workout_date": "2025-08-12"
}
```

#### Get Workouts (with filtering)
```http
GET /api/workouts?date=2025-08-12&exercise=bench
Authorization: Bearer <your_token>
```

#### Update Workout Set
```http
PUT /api/workouts/{id}
Authorization: Bearer <your_token>
Content-Type: application/json

{
    "weight": 140.0,
    "reps": 8
}
```

#### Duplicate Workout
```http
POST /api/workouts/{id}/duplicate
Authorization: Bearer <your_token>
Content-Type: application/json

{
    "workout_date": "2025-08-13"
}
```

### Analytics Endpoints

#### Get Exercise Progress
```http
GET /api/analytics/progress/Bench%20Press
Authorization: Bearer <your_token>
```

#### Get Workout Summary
```http
GET /api/analytics/summary?date_from=2025-08-01&date_to=2025-08-31
Authorization: Bearer <your_token>
```

## 💻 Client Integration

### Python Client

```python
from client import WorkoutAPIClient

# Initialize client
client = WorkoutAPIClient("http://localhost:8000")

# Register and login
user = client.register("testuser", "test@example.com", "password123")

# Add workout
workout = client.add_workout_set("Bench Press", 135.5, 10)

# Get workouts
workouts = client.get_workouts(exercise="bench")

# Get progress
progress = client.get_exercise_progress("Bench Press")
```

### JavaScript/TypeScript Client

```javascript
import { WorkoutAPIClient } from './client.js';

const client = new WorkoutAPIClient('http://localhost:8000');

// Login
const user = await client.login('testuser', 'password123');

// Add workout
const workout = await client.addWorkoutSet('Bench Press', 135.5, 10);

// Get workouts with filtering
const workouts = await client.getWorkouts({
    date_from: '2025-08-01',
    date_to: '2025-08-31',
    exercise: 'bench'
});

// Get analytics
const exercises = await client.getExercises();
const summary = await client.getWorkoutSummary();
```

### React Integration Example

```jsx
import { useState, useEffect } from 'react';
import { WorkoutAPIClient } from './api/client';

const WorkoutDashboard = () => {
    const [workouts, setWorkouts] = useState([]);
    const [client] = useState(new WorkoutAPIClient());

    useEffect(() => {
        const loadWorkouts = async () => {
            try {
                const data = await client.getWorkouts();
                setWorkouts(data);
            } catch (error) {
                console.error('Failed to load workouts:', error);
            }
        };
        
        loadWorkouts();
    }, []);

    const addWorkout = async (exercise, weight, reps) => {
        try {
            const workout = await client.addWorkoutSet(exercise, weight, reps);
            setWorkouts([workout, ...workouts]);
        } catch (error) {
            console.error('Failed to add workout:', error);
        }
    };

    return (
        <div>
            <h1>Workout Tracker</h1>
            {/* Your UI components here */}
        </div>
    );
};
```

## 🏗️ Database Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workout sets table
CREATE TABLE workout_sets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exercise VARCHAR NOT NULL,
    weight DECIMAL NOT NULL,
    reps INTEGER NOT NULL,
    workout_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🧪 Testing

### Run All Tests
```bash
# Using the setup script
python setup.py test

# Using pytest directly
pytest test_api.py -v

# With coverage
pytest test_api.py --cov=main --cov-report=html
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end API testing
- **Performance Tests**: Load and stress testing
- **Security Tests**: Authentication and authorization

## 🐳 Docker Deployment

### Development
```bash
docker-compose -f docker-compose.yml up --build
```

### Production
```bash
# Copy production environment
cp .env.example .env.prod
# Edit .env.prod with production values

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Services
- **API Server**: FastAPI application (port 8000)
- **Database**: PostgreSQL 15 (port 5432)
- **Cache**: Redis 7 (port 6379)
- **Proxy**: Nginx with SSL (ports 80, 443)

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask session secret | Required |
| `JWT_SECRET_KEY` | JWT signing secret | Required |
| `DATABASE_URL` | Database connection string | `sqlite:///./workout_tracker.db` |
| `ENVIRONMENT` | Deployment environment | `development` |
| `API_HOST` | Server bind address | `0.0.0.0` |
| `API_PORT` | Server port | `8000` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration time | `1440` (24h) |

### Database Support

- **SQLite**: For development and testing
- **PostgreSQL**: Recommended for production
- **MySQL**: Alternative production option

### Caching

- **Redis**: Optional caching layer
- **In-Memory**: Fallback for development

## 🚀 Production Deployment

### Server Requirements
- **Python**: 3.8 or higher
- **RAM**: Minimum 512MB, recommended 2GB+
- **Storage**: Minimum 1GB for application and database
- **CPU**: 1+ cores (2+ recommended)

### Deployment Options

#### 1. Traditional Server
```bash
# Setup production environment
python setup.py production

# Configure systemd service
sudo systemctl start workout-api
sudo systemctl enable workout-api

# Configure Nginx reverse proxy
sudo cp nginx.conf /etc/nginx/sites-available/workout-api
sudo ln -s /etc/nginx/sites-available/workout-api /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

#### 2. Docker Container
```bash
# Build production image
docker build -t workout-api:prod .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

#### 3. Cloud Platforms

**AWS ECS/Fargate**
```bash
# Build and push to ECR
aws ecr create-repository --repository-name workout-api
docker tag workout-api:prod <account>.dkr.ecr.<region>.amazonaws.com/workout-api:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/workout-api:latest
```

**Google Cloud Run**
```bash
# Deploy to Cloud Run
gcloud builds submit --tag gcr.io/<project>/workout-api
gcloud run deploy --image gcr.io/<project>/workout-api --platform managed
```

**Heroku**
```bash
# Deploy to Heroku
heroku create your-workout-api
heroku addons:create heroku-postgresql:mini
git push heroku main
```

### SSL/TLS Setup

```bash
# Using Let's Encrypt with Certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
sudo systemctl enable certbot.timer
```

## 📊 Monitoring & Analytics

### Health Checks
```bash
curl http://localhost:8000/health
```

### Metrics Collection
- Request/response times
- Error rates
- Database performance
- User activity patterns

### Logging
```python
# Structured JSON logging
{
    "timestamp": "2025-08-12T10:00:00Z",
    "level": "INFO",
    "message": "User logged in",
    "user_id": 123,
    "ip_address": "192.168.1.1"
}
```

## 🤝 Contributing

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/fastapi-workout-tracker.git
cd fastapi-workout-tracker

# Setup development environment
python setup.py dev

# Create a feature branch
git checkout -b feature/awesome-feature

# Make your changes and test
python setup.py test

# Commit and push
git commit -m "Add awesome feature"
git push origin feature/awesome-feature
```

### Coding Standards
- Follow PEP 8 style guide
- Use type hints
- Write comprehensive tests
- Document public APIs
- Keep commits atomic and descriptive

### Pull Request Process
1. Update documentation
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Submit pull request with description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI**: For the amazing Python web framework
- **SQLAlchemy**: For powerful database ORM
- **Pydantic**: For data validation and serialization
- **JWT**: For secure authentication
- **Docker**: For containerization
- **PostgreSQL**: For robust database storage

## 📞 Support

- **Documentation**: http://localhost:8000/docs
- **Issues**: [GitHub Issues](https://github.com/yourusername/fastapi-workout-tracker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/fastapi-workout-tracker/discussions)

---

**Built with ❤️ using FastAPI**

*Start tracking your workouts today! 🏋️‍♀️*