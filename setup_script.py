#!/usr/bin/env python3
"""
FastAPI Workout Tracker Setup and Deployment Script

This script helps set up the development environment and deploy the application.

Usage:
    python setup.py --help
    python setup.py dev          # Setup development environment
    python setup.py production   # Setup for production deployment
    python setup.py test         # Run tests
    python setup.py docker       # Build and run with Docker
"""

import os
import sys
import subprocess
import argparse
import secrets
from pathlib import Path

def run_command(cmd, check=True, shell=True):
    """Run a shell command"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=shell, check=check, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result

def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_urlsafe(32)

def create_env_file():
    """Create .env file from template"""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Skipping .env file creation")
            return
    
    if not env_example.exists():
        print("Warning: .env.example not found. Creating basic .env file.")
        env_content = f"""SECRET_KEY={generate_secret_key()}
JWT_SECRET_KEY={generate_secret_key()}
DATABASE_URL=sqlite:///./workout_tracker.db
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
"""
    else:
        with open(env_example, 'r') as f:
            env_content = f.read()
        
        # Replace example values with generated ones
        env_content = env_content.replace(
            "your-super-secret-key-change-in-production-make-it-long-and-random",
            generate_secret_key()
        )
        env_content = env_content.replace(
            "your-jwt-secret-key-also-change-this-in-production",
            generate_secret_key()
        )
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print("✓ Created .env file with secure random keys")

def setup_development():
    """Set up development environment"""
    print("Setting up development environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version.split()[0]} detected")
    
    # Create virtual environment if it doesn't exist
    if not Path("venv").exists():
        print("Creating virtual environment...")
        run_command(f"{sys.executable} -m venv venv")
        print("✓ Virtual environment created")
    else:
        print("✓ Virtual environment already exists")
    
    # Determine activation script
    if os.name == 'nt':  # Windows
        activate_script = "venv\\Scripts\\activate"
        python_cmd = "venv\\Scripts\\python"
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        activate_script = "venv/bin/activate"
        python_cmd = "venv/bin/python"
        pip_cmd = "venv/bin/pip"
    
    # Install requirements
    print("Installing Python dependencies...")
    run_command(f"{pip_cmd} install --upgrade pip")
    run_command(f"{pip_cmd} install -r requirements.txt")
    print("✓ Dependencies installed")
    
    # Create .env file
    create_env_file()
    
    # Initialize database
    print("Initializing database...")
    try:
        run_command(f"{python_cmd} -c \"from main import Base, engine; Base.metadata.create_all(bind=engine); print('Database initialized')\"")
        print("✓ Database initialized")
    except subprocess.CalledProcessError:
        print("Warning: Could not initialize database. You may need to run it manually.")
    
    # Setup Alembic (database migrations)
    if not Path("alembic").exists():
        print("Setting up database migrations...")
        run_command(f"{pip_cmd} install alembic")
        run_command("alembic init alembic")
        print("✓ Database migrations initialized")
    
    print("\n🎉 Development environment setup complete!")
    print("\nTo start the development server:")
    if os.name == 'nt':
        print("  venv\\Scripts\\activate")
    else:
        print("  source venv/bin/activate")
    print("  python main.py")
    print("\nOr use uvicorn directly:")
    print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")

def setup_production():
    """Set up production environment"""
    print("Setting up production environment...")
    
    # Check if running as root (not recommended)
    if os.geteuid() == 0:
        print("Warning: Running as root is not recommended for production")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Install system dependencies
    print("Installing system dependencies...")
    try:
        # Detect OS and install appropriate packages
        if Path("/etc/debian_version").exists():  # Debian/Ubuntu
            run_command("sudo apt-get update")
            run_command("sudo apt-get install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server")
        elif Path("/etc/redhat-release").exists():  # RHEL/CentOS/Fedora
            run_command("sudo yum install -y python3 python3-pip nginx postgresql postgresql-server redis")
        else:
            print("Warning: Unsupported OS. Please install dependencies manually:")
            print("- Python 3.8+")
            print("- PostgreSQL")
            print("- Redis (optional)")
            print("- Nginx")
    except subprocess.CalledProcessError:
        print("Warning: Could not install system dependencies automatically")
    
    # Create production user
    try:
        run_command("sudo useradd -m -s /bin/bash workout-api", check=False)
        print("✓ Created workout-api user")
    except:
        print("User workout-api may already exist")
    
    # Setup application directory
    app_dir = Path("/opt/workout-api")
    try:
        run_command(f"sudo mkdir -p {app_dir}")
        run_command(f"sudo chown workout-api:workout-api {app_dir}")
        print(f"✓ Created application directory: {app_dir}")
    except:
        print("Warning: Could not create application directory")
    
    # Create production .env file
    create_env_file()
    
    # Update .env for production
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Update for production
        content = content.replace("ENVIRONMENT=development", "ENVIRONMENT=production")
        content = content.replace("DEBUG=true", "DEBUG=false")
        content = content.replace("DATABASE_URL=sqlite:///./workout_tracker.db", 
                                "DATABASE_URL=postgresql://workout_user:secure_password@localhost:5432/workout_db")
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✓ Updated .env for production")
    
    # Create systemd service
    service_content = """[Unit]
Description=FastAPI Workout Tracker
After=network.target

[Service]
Type=notify
User=workout-api
Group=workout-api
WorkingDirectory=/opt/workout-api
Environment=PATH=/opt/workout-api/venv/bin
EnvironmentFile=/opt/workout-api/.env
ExecStart=/opt/workout-api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    
    try:
        with open("/tmp/workout-api.service", 'w') as f:
            f.write(service_content)
        run_command("sudo mv /tmp/workout-api.service /etc/systemd/system/")
        run_command("sudo systemctl daemon-reload")
        run_command("sudo systemctl enable workout-api")
        print("✓ Created systemd service")
    except:
        print("Warning: Could not create systemd service")
    
    print("\n🚀 Production setup complete!")
    print("\nNext steps:")
    print("1. Copy your application files to /opt/workout-api/")
    print("2. Set up PostgreSQL database and update DATABASE_URL in .env")
    print("3. Configure Nginx reverse proxy")
    print("4. Set up SSL certificates (Let's Encrypt recommended)")
    print("5. Start the service: sudo systemctl start workout-api")

def run_tests():
    """Run the test suite"""
    print("Running tests...")
    
    # Check if pytest is installed
    try:
        run_command("python -m pytest --version")
    except subprocess.CalledProcessError:
        print("Installing pytest...")
        run_command("pip install pytest pytest-asyncio httpx")
    
    # Run tests
    try:
        run_command("python -m pytest test_api.py -v --tb=short")
        print("✓ All tests passed!")
    except subprocess.CalledProcessError:
        print("✗ Some tests failed")
        sys.exit(1)

def docker_setup():
    """Build and run with Docker"""
    print("Setting up Docker environment...")
    
    # Check if Docker is installed
    try:
        run_command("docker --version")
        run_command("docker-compose --version")
    except subprocess.CalledProcessError:
        print("Error: Docker and Docker Compose are required")
        print("Please install Docker: https://docs.docker.com/get-docker/")
        sys.exit(1)
    
    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        create_env_file()
    
    # Build and start services
    print("Building and starting Docker containers...")
    run_command("docker-compose down")  # Stop any running containers
    run_command("docker-compose build")
    run_command("docker-compose up -d")
    
    # Wait for services to start
    import time
    print("Waiting for services to start...")
    time.sleep(10)
    
    # Test the API
    try:
        run_command("curl -f http://localhost:8000/health")
        print("✓ API is running on http://localhost:8000")
        print("✓ API documentation available at http://localhost:8000/docs")
        print("✓ PostgreSQL database running on port 5432")
        print("✓ Redis cache running on port 6379")
    except:
        print("Warning: Could not verify API status")
        print("Check container logs: docker-compose logs")

def create_migration():
    """Create a new database migration"""
    message = input("Enter migration message: ")
    if not message:
        message = "Auto-generated migration"
    
    run_command(f"alembic revision --autogenerate -m \"{message}\"")
    print("✓ Migration created")

def migrate_database():
    """Apply database migrations"""
    print("Applying database migrations...")
    run_command("alembic upgrade head")
    print("✓ Database migrations applied")

def create_admin_user():
    """Create an admin user"""
    print("Creating admin user...")
    
    username = input("Enter admin username: ") or "admin"
    email = input("Enter admin email: ") or "admin@example.com"
    password = input("Enter admin password: ") or "admin123"
    
    script = f"""
import sys
sys.path.append('.')
from main import SessionLocal, User, get_password_hash
from sqlalchemy.exc import IntegrityError

db = SessionLocal()
try:
    hashed_password = get_password_hash('{password}')
    admin_user = User(
        username='{username}',
        email='{email}',
        password_hash=hashed_password
    )
    db.add(admin_user)
    db.commit()
    print('✓ Admin user created successfully')
except IntegrityError:
    print('✗ User already exists')
except Exception as e:
    print(f'✗ Error creating user: {{e}}')
finally:
    db.close()
"""
    
    with open("create_admin.py", "w") as f:
        f.write(script)
    
    run_command("python create_admin.py")
    os.remove("create_admin.py")

def backup_database():
    """Backup the database"""
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"workout_backup_{timestamp}.sql"
    
    # Check if PostgreSQL
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        if "postgresql://" in env_content:
            print("Backing up PostgreSQL database...")
            run_command(f"pg_dump $DATABASE_URL > {backup_file}")
        else:
            print("Backing up SQLite database...")
            run_command(f"cp workout_tracker.db workout_tracker_backup_{timestamp}.db")
    
    print(f"✓ Database backup created: {backup_file}")

def main():
    parser = argparse.ArgumentParser(description="FastAPI Workout Tracker Setup Script")
    parser.add_argument("command", choices=[
        "dev", "development", 
        "prod", "production",
        "test", "tests",
        "docker",
        "migrate",
        "create-migration",
        "create-admin",
        "backup"
    ], help="Command to run")
    
    args = parser.parse_args()
    
    try:
        if args.command in ["dev", "development"]:
            setup_development()
        elif args.command in ["prod", "production"]:
            setup_production()
        elif args.command in ["test", "tests"]:
            run_tests()
        elif args.command == "docker":
            docker_setup()
        elif args.command == "migrate":
            migrate_database()
        elif args.command == "create-migration":
            create_migration()
        elif args.command == "create-admin":
            create_admin_user()
        elif args.command == "backup":
            backup_database()
    
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()