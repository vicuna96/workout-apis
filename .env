# FastAPI Workout Tracker Environment Configuration
# Copy this file to .env and update with your values

# Application Settings
SECRET_KEY=your-super-secret-key-change-in-production-make-it-long-and-random
JWT_SECRET_KEY=your-jwt-secret-key-also-change-this-in-production
ENVIRONMENT=development

# Database Configuration
# SQLite (for development)
DATABASE_URL=sqlite:///./workout_tracker.db

# PostgreSQL (for production)
# DATABASE_URL=postgresql://username:password@localhost:5432/workout_db

# MySQL (alternative)
# DATABASE_URL=mysql://username:password@localhost:3306/workout_db

# JWT Settings
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
ALGORITHM=HS256

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# CORS Settings (comma-separated origins)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080,https://yourdomain.com

# Redis Configuration (optional, for caching)
REDIS_URL=redis://localhost:6379/0

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_SECOND=10
RATE_LIMIT_BURST=20

# Email Configuration (for future features)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# File Upload Settings
MAX_FILE_SIZE=10485760  # 10MB in bytes
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif

# Security Headers
SECURITY_HEADERS_ENABLED=true

# Monitoring and Analytics
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENABLE_METRICS=true

# Development Settings
DEBUG=false
RELOAD=true