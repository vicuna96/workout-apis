"""
Comprehensive test suite for the FastAPI Workout Tracker API

Run with: python -m pytest test_api.py -v
"""

import pytest
import httpx
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta
from main import app, get_db, Base, engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_workout_tracker.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)
    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Create test database
    Base.metadata.create_all(bind=test_engine)
    yield
    # Clean up
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_workout_tracker.db"):
        os.remove("./test_workout_tracker.db")

@pytest.fixture(scope="function")
def client(db_session):
    # Override get_db to always yield the same session for this test
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # cleanup handled by fixture

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

@pytest.fixture
def test_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }

@pytest.fixture
def authenticated_client(client, test_user_data):
    # Register and login user
    response = client.post("/api/auth/register", json=test_user_data)
    if response.status_code == 400:
        response = client.post("/api/auth/login", json=test_user_data)
        assert response.status_code == 200
    else:
        assert response.status_code == 201

    token = response.json()["access_token"]
    
    # Return client with authentication headers
    class AuthenticatedClient:
        def __init__(self, client, token):
            self._client = client
            self._token = token
            self.headers = {"Authorization": f"Bearer {token}"}
        
        def get(self, *args, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self._client.get(*args, **kwargs)
        
        def post(self, *args, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self._client.post(*args, **kwargs)
        
        def put(self, *args, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self._client.put(*args, **kwargs)
        
        def delete(self, *args, **kwargs):
            kwargs.setdefault('headers', {}).update(self.headers)
            return self._client.delete(*args, **kwargs)
    
    return AuthenticatedClient(client, token)

class TestHealthCheck:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "2.0.0"

class TestAuthentication:
    def test_register_user_success(self, client, test_user_data):
        response = client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert "access_token" in data
        assert data["user"]["username"] == test_user_data["username"]
        assert data["user"]["email"] == test_user_data["email"]
        assert "password" not in data["user"]
    
    def test_register_user_duplicate_username(self, client, test_user_data):
        # Register first user
        client.post("/api/auth/register", json=test_user_data)
        
        # Try to register same username
        response = client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    def test_register_user_invalid_data(self, client):
        # Test short username
        response = client.post("/api/auth/register", json={
            "username": "ab",  # Too short
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 422
        
        # Test invalid email
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123"
        })
        assert response.status_code == 422
        
        # Test short password
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "12345"  # Too short
        })
        assert response.status_code == 422
    
    def test_login_success(self, client, test_user_data):
        # Register user first
        client.post("/api/auth/register", json=test_user_data)
        
        # Login with username
        response = client.post("/api/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Login successful"
        assert "access_token" in data
        assert data["user"]["username"] == test_user_data["username"]
        
        # Login with email
        response = client.post("/api/auth/login", json={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        assert response.status_code == 200
    
    def test_login_invalid_credentials(self, client, test_user_data):
        # Register user first
        client.post("/api/auth/register", json=test_user_data)
        
        # Wrong password
        response = client.post("/api/auth/login", json={
            "username": test_user_data["username"],
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        
        # Non-existent user
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "password123"
        })
        assert response.status_code == 401
    
    def test_get_current_user(self, authenticated_client):
        response = authenticated_client.get("/api/auth/me")
        assert response.status_code == 200
        
        data = response.json()
        assert "user" in data
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"
    
    def test_get_current_user_unauthorized(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 403

class TestWorkouts:
    def test_create_workout_set(self, authenticated_client):
        workout_data = {
            "exercise": "Bench Press",
            "weight": 135.5,
            "reps": 10,
            "workout_date": "2025-08-12"
        }
        
        response = authenticated_client.post("/api/workouts", json=workout_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["message"] == "Workout set created successfully"
        workout = data["workout_set"]
        assert workout["exercise"] == workout_data["exercise"]
        assert workout["weight"] == workout_data["weight"]
        assert workout["reps"] == workout_data["reps"]
        assert workout["volume"] == workout_data["weight"] * workout_data["reps"]
        assert "id" in workout
        assert "created_at" in workout
    
    def test_create_workout_set_unauthorized(self, client):
        workout_data = {
            "exercise": "Bench Press",
            "weight": 135.5,
            "reps": 10,
            "workout_date": "2025-08-12"
        }
        
        response = client.post("/api/workouts", json=workout_data)
        assert response.status_code == 403
    
    def test_get_workout_sets(self, authenticated_client):
        # Create some workout sets
        workouts = [
            {"exercise": "Bench Press", "weight": 135.5, "reps": 10, "workout_date": "2025-08-12"},
            {"exercise": "Deadlift", "weight": 225.0, "reps": 5, "workout_date": "2025-08-12"},
            {"exercise": "Squat", "weight": 185.0, "reps": 8, "workout_date": "2025-08-13"},
        ]
        
        for workout in workouts:
            authenticated_client.post("/api/workouts", json=workout)
        
        # Get all workouts
        response = authenticated_client.get("/api/workouts")
        assert response.status_code == 200
        
        data = response.json()
        assert "workout_sets" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["workout_sets"]) == 3
    
    def test_get_workout_sets_with_filters(self, authenticated_client):
        # Create workout sets on different dates
        workouts = [
            {"exercise": "Bench Press", "weight": 135.5, "reps": 10, "workout_date": "2025-08-12"},
            {"exercise": "Deadlift", "weight": 225.0, "reps": 5, "workout_date": "2025-08-13"},
            {"exercise": "Bench Press", "weight": 140.0, "reps": 8, "workout_date": "2025-08-14"},
        ]
        
        for workout in workouts:
            authenticated_client.post("/api/workouts", json=workout)
        
        # Filter by date
        response = authenticated_client.get("/api/workouts?date=2025-08-12")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        
        # Filter by date range
        response = authenticated_client.get("/api/workouts?date_from=2025-08-12&date_to=2025-08-13")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        
        # Filter by exercise
        response = authenticated_client.get("/api/workouts?exercise=Bench")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
    
    def test_get_specific_workout_set(self, authenticated_client):
        # Create a workout set
        workout_data = {
            "exercise": "Bench Press",
            "weight": 135.5,
            "reps": 10,
            "workout_date": "2025-08-12"
        }
        
        response = authenticated_client.post("/api/workouts", json=workout_data)
        workout_id = response.json()["workout_set"]["id"]
        
        # Get specific workout set
        response = authenticated_client.get(f"/api/workouts/{workout_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "workout_set" in data
        assert data["workout_set"]["id"] == workout_id
        assert data["workout_set"]["exercise"] == workout_data["exercise"]
    
    def test_get_nonexistent_workout_set(self, authenticated_client):
        response = authenticated_client.get("/api/workouts/999")
        assert response.status_code == 404
    
    def test_update_workout_set(self, authenticated_client):
        # Create a workout set
        workout_data = {
            "exercise": "Bench Press",
            "weight": 135.5,
            "reps": 10,
            "workout_date": "2025-08-12"
        }
        
        response = authenticated_client.post("/api/workouts", json=workout_data)
        workout_id = response.json()["workout_set"]["id"]
        
        # Update the workout set
        update_data = {
            "weight": 140.0,
            "reps": 8
        }
        
        response = authenticated_client.put(f"/api/workouts/{workout_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Workout set updated successfully"
        workout = data["workout_set"]
        assert workout["weight"] == 140.0
        assert workout["reps"] == 8
        assert workout["exercise"] == "Bench Press"  # Unchanged
        assert workout["volume"] == 140.0 * 8
    
    def test_delete_workout_set(self, authenticated_client):
        # Create a workout set
        workout_data = {
            "exercise": "Bench Press",
            "weight": 135.5,
            "reps": 10,
            "workout_date": "2025-08-12"
        }
        
        response = authenticated_client.post("/api/workouts", json=workout_data)
        workout_id = response.json()["workout_set"]["id"]
        
        # Delete the workout set
        response = authenticated_client.delete(f"/api/workouts/{workout_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Workout set deleted successfully"
        
        # Verify it's deleted
        response = authenticated_client.get(f"/api/workouts/{workout_id}")
        assert response.status_code == 404
    
    def test_duplicate_workout_set(self, authenticated_client):
        # Create a workout set
        workout_data = {
            "exercise": "Bench Press",
            "weight": 135.5,
            "reps": 10,
            "workout_date": "2025-08-12"
        }
        
        response = authenticated_client.post("/api/workouts", json=workout_data)
        workout_id = response.json()["workout_set"]["id"]
        
        # Duplicate with new date
        duplicate_data = {"workout_date": "2025-08-13"}
        response = authenticated_client.post(f"/api/workouts/{workout_id}/duplicate", json=duplicate_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["message"] == "Workout set duplicated successfully"
        duplicated_workout = data["workout_set"]
        assert duplicated_workout["exercise"] == workout_data["exercise"]
        assert duplicated_workout["weight"] == workout_data["weight"]
        assert duplicated_workout["reps"] == workout_data["reps"]
        assert duplicated_workout["workout_date"] == "2025-08-13"
        assert duplicated_workout["id"] != workout_id

class TestAnalytics:
    def test_get_exercise_list(self, authenticated_client):
        # Create some workout sets with different exercises
        workouts = [
            {"exercise": "Bench Press", "weight": 135.5, "reps": 10, "workout_date": "2025-08-12"},
            {"exercise": "Deadlift", "weight": 225.0, "reps": 5, "workout_date": "2025-08-12"},
            {"exercise": "Squat", "weight": 185.0, "reps": 8, "workout_date": "2025-08-13"},
            {"exercise": "Bench Press", "weight": 140.0, "reps": 8, "workout_date": "2025-08-13"},
        ]
        
        for workout in workouts:
            authenticated_client.post("/api/workouts", json=workout)
        
        # Get exercise list
        response = authenticated_client.get("/api/analytics/exercises")
        assert response.status_code == 200
        
        data = response.json()
        assert "exercises" in data
        exercises = data["exercises"]
        assert len(exercises) == 3
        assert "Bench Press" in exercises
        assert "Deadlift" in exercises
        assert "Squat" in exercises
    
    def test_get_exercise_progress(self, authenticated_client):
        # Create multiple sets of the same exercise over different days
        workouts = [
            {"exercise": "Bench Press", "weight": 135.0, "reps": 10, "workout_date": "2025-08-10"},
            {"exercise": "Bench Press", "weight": 135.0, "reps": 8, "workout_date": "2025-08-10"},
            {"exercise": "Bench Press", "weight": 140.0, "reps": 10, "workout_date": "2025-08-12"},
            {"exercise": "Bench Press", "weight": 140.0, "reps": 8, "workout_date": "2025-08-12"},
        ]
        
        for workout in workouts:
            authenticated_client.post("/api/workouts", json=workout)
        
        # Get progress for Bench Press
        response = authenticated_client.get("/api/analytics/progress/Bench Press")
        assert response.status_code == 200
        
        data = response.json()
        assert data["exercise"] == "Bench Press"
        assert data["total_workouts"] == 2  # 2 different dates
        assert data["total_sets"] == 4
        
        progress_data = data["progress_data"]
        assert len(progress_data) == 2
        
        # Check first day (2025-08-10)
        day1 = next(p for p in progress_data if p["date"] == "2025-08-10")
        assert day1["max_weight"] == 135.0
        assert day1["avg_weight"] == 135.0
        assert day1["sets"] == 2
        assert day1["total_volume"] == (135.0 * 10) + (135.0 * 8)
        
        # Check second day (2025-08-12)
        day2 = next(p for p in progress_data if p["date"] == "2025-08-12")
        assert day2["max_weight"] == 140.0
        assert day2["avg_weight"] == 140.0
        assert day2["sets"] == 2
        assert day2["total_volume"] == (140.0 * 10) + (140.0 * 8)
    
    def test_get_workout_summary(self, authenticated_client):
        # Create workout sets across multiple days and exercises
        workouts = [
            {"exercise": "Bench Press", "weight": 135.5, "reps": 10, "workout_date": "2025-08-10"},
            {"exercise": "Deadlift", "weight": 225.0, "reps": 5, "workout_date": "2025-08-10"},
            {"exercise": "Bench Press", "weight": 140.0, "reps": 8, "workout_date": "2025-08-12"},
            {"exercise": "Squat", "weight": 185.0, "reps": 8, "workout_date": "2025-08-14"},
        ]
        
        for workout in workouts:
            authenticated_client.post("/api/workouts", json=workout)
        
        # Get overall summary
        response = authenticated_client.get("/api/analytics/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_sets"] == 4
        assert data["workout_days"] == 3  # 3 different dates
        assert data["exercises"] == 3  # Bench Press, Deadlift, Squat
        
        expected_volume = (135.5 * 10) + (225.0 * 5) + (140.0 * 8) + (185.0 * 8)
        assert data["total_volume"] == expected_volume
        
        # Test with date range
        response = authenticated_client.get("/api/analytics/summary?date_from=2025-08-10&date_to=2025-08-12")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_sets"] == 3  # First 3 workouts only
        assert data["workout_days"] == 2  # 2 days in range

class TestIntegration:
    """Integration tests that test complete workflows"""
    
    def test_complete_workout_flow(self, client):
        # 1. Register user
        user_data = {
            "username": "integrateduser",
            "email": "integrated@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Add multiple workout sets
        workouts = [
            {"exercise": "Bench Press", "weight": 135.0, "reps": 10, "workout_date": "2025-08-10"},
            {"exercise": "Bench Press", "weight": 140.0, "reps": 8, "workout_date": "2025-08-12"},
            {"exercise": "Deadlift", "weight": 225.0, "reps": 5, "workout_date": "2025-08-12"},
        ]
        
        workout_ids = []
        for workout in workouts:
            response = client.post("/api/workouts", json=workout, headers=headers)
            assert response.status_code == 201
            workout_ids.append(response.json()["workout_set"]["id"])
        
        # 3. Get all workouts and verify
        response = client.get("/api/workouts", headers=headers)
        assert response.status_code == 200
        assert response.json()["total"] == 3
        
        # 4. Update a workout
        update_data = {"weight": 142.5}
        response = client.put(f"/api/workouts/{workout_ids[1]}", json=update_data, headers=headers)
        assert response.status_code == 200
        assert response.json()["workout_set"]["weight"] == 142.5
        
        # 5. Duplicate a workout
        response = client.post(f"/api/workouts/{workout_ids[0]}/duplicate", 
                             json={"workout_date": "2025-08-15"}, headers=headers)
        assert response.status_code == 201
        duplicated_id = response.json()["workout_set"]["id"]
        
        # 6. Get analytics
        response = client.get("/api/analytics/exercises", headers=headers)
        assert response.status_code == 200
        exercises = response.json()["exercises"]
        assert "Bench Press" in exercises
        assert "Deadlift" in exercises
        
        # 7. Get progress for Bench Press
        response = client.get("/api/analytics/progress/Bench Press", headers=headers)
        assert response.status_code == 200
        progress = response.json()
        assert progress["total_sets"] == 3  # Original 2 + duplicated 1
        assert progress["total_workouts"] == 3  # 3 different dates
        
        # 8. Get summary
        response = client.get("/api/analytics/summary", headers=headers)
        assert response.status_code == 200
        summary = response.json()
        assert summary["total_sets"] == 4  # 3 original + 1 duplicated
        assert summary["exercises"] == 2  # Bench Press and Deadlift
        
        # 9. Delete a workout
        response = client.delete(f"/api/workouts/{duplicated_id}", headers=headers)
        assert response.status_code == 200
        
        # 10. Verify deletion
        response = client.get("/api/workouts", headers=headers)
        assert response.status_code == 200
        assert response.json()["total"] == 3  # Back to 3 workouts

# Performance and stress tests
class TestPerformance:
    def test_bulk_workout_creation(self, authenticated_client):
        """Test creating many workout sets"""
        workouts = []
        for i in range(50):
            workouts.append({
                "exercise": f"Exercise {i % 5}",  # 5 different exercises
                "weight": 100 + (i * 2.5),
                "reps": 8 + (i % 5),
                "workout_date": f"2025-08-{10 + (i % 20)}"  # Spread across 20 days
            })
        
        # Create all workouts
        for workout in workouts:
            response = authenticated_client.post("/api/workouts", json=workout)
            assert response.status_code == 201
        
        # Verify all were created
        response = authenticated_client.get("/api/workouts")
        assert response.status_code == 200
        assert response.json()["total"] == 50
        
        # Test analytics with large dataset
        response = authenticated_client.get("/api/analytics/exercises")
        assert response.status_code == 200
        assert len(response.json()["exercises"]) == 5
        
        response = authenticated_client.get("/api/analytics/summary")
        assert response.status_code == 200
        summary = response.json()
        assert summary["total_sets"] == 50

if __name__ == "__main__":
    # Run basic tests without pytest
    import requests
    import json
    
    print("Running basic API integration test...")
    
    BASE_URL = "http://localhost:8000"
    
    # Test health check
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Health check passed")
        else:
            print("✗ Health check failed")
            exit(1)
    except requests.exceptions.RequestException:
        print("✗ Cannot connect to API. Make sure it's running on http://localhost:8000")
        exit(1)
    
    # Test registration
    user_data = {
        "username": "testapi",
        "email": "testapi@example.com", 
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    if response.status_code == 201:
        print("✓ User registration passed")
        token = response.json()["access_token"]
    else:
        print("✗ User registration failed:", response.json())
        exit(1)
    
    # Test adding workout
    headers = {"Authorization": f"Bearer {token}"}
    workout_data = {
        "exercise": "Test Exercise",
        "weight": 100.0,
        "reps": 10,
        "workout_date": "2025-08-12"
    }
    
    response = requests.post(f"{BASE_URL}/api/workouts", json=workout_data, headers=headers)
    if response.status_code == 201:
        print("✓ Workout creation passed")
    else:
        print("✗ Workout creation failed:", response.json())
        exit(1)
    
    # Test getting workouts
    response = requests.get(f"{BASE_URL}/api/workouts", headers=headers)
    if response.status_code == 200 and response.json()["total"] > 0:
        print("✓ Workout retrieval passed")
    else:
        print("✗ Workout retrieval failed")
        print("✗ You may need to clear the db if the test was previously ran in the same environment.")
        exit(1)
    
    print("\n🎉 All basic integration tests passed!")
    print("\nTo run comprehensive tests:")
    print("1. Install pytest: pip install pytest pytest-asyncio")
    print("2. Run: python -m pytest test_api.py -v")