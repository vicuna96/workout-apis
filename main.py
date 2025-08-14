from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr, validator
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import os
from contextlib import asynccontextmanager

# Environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-here")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./workout_tracker.db")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    workout_sets = relationship("WorkoutSet", back_populates="user", cascade="all, delete-orphan")

class WorkoutSet(Base):
    __tablename__ = "workout_sets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    reps = Column(Integer, nullable=False)
    workout_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="workout_sets")
    
    @property
    def volume(self) -> float:
        return self.weight * self.reps

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    @validator('username')
    def username_length(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        return v
    
    @validator('password')
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class WorkoutSetCreate(BaseModel):
    exercise: str
    weight: float
    reps: int
    workout_date: date

class WorkoutSetUpdate(BaseModel):
    exercise: Optional[str] = None
    weight: Optional[float] = None
    reps: Optional[int] = None
    workout_date: Optional[date] = None

class WorkoutSetResponse(BaseModel):
    id: int
    exercise: str
    weight: float
    reps: int
    workout_date: date
    created_at: datetime
    volume: float
    
    class Config:
        from_attributes = True

class WorkoutSetDuplicate(BaseModel):
    workout_date: Optional[date] = None

class ProgressData(BaseModel):
    date: date
    max_weight: float
    avg_weight: float
    total_volume: float
    sets: int

class ExerciseProgress(BaseModel):
    exercise: str
    progress_data: List[ProgressData]
    total_workouts: int
    total_sets: int

class WorkoutSummary(BaseModel):
    total_sets: int
    total_volume: float
    workout_days: int
    exercises: int
    date_range: Dict[str, Optional[date]]

# Utility functions
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown (cleanup if needed)

# FastAPI app
app = FastAPI(
    title="Workout Tracker API",
    description="A comprehensive REST API for tracking workouts, built with FastAPI",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "2.0.0"
    }

# Authentication endpoints
@app.post("/api/auth/register", response_model=dict, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": db_user.username})
    
    return {
        "message": "User registered successfully",
        "access_token": access_token,
        "user": UserResponse.from_orm(db_user)
    }

@app.post("/api/auth/login", response_model=dict, tags=["Authentication"])
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == user_credentials.username) | 
        (User.email == user_credentials.username)
    ).first()
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "message": "Login successful",
        "access_token": access_token,
        "user": UserResponse.from_orm(user)
    }

@app.get("/api/auth/me", response_model=dict, tags=["Authentication"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {"user": UserResponse.from_orm(current_user)}

# Workout endpoints
@app.post("/api/workouts", response_model=dict, status_code=status.HTTP_201_CREATED, tags=["Workouts"])
async def create_workout_set(
    workout_data: WorkoutSetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_workout = WorkoutSet(
        user_id=current_user.id,
        exercise=workout_data.exercise,
        weight=workout_data.weight,
        reps=workout_data.reps,
        workout_date=workout_data.workout_date
    )
    
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    
    return {
        "message": "Workout set created successfully",
        "workout_set": WorkoutSetResponse.from_orm(db_workout)
    }

@app.get("/api/workouts", response_model=dict, tags=["Workouts"])
async def get_workout_sets(
    date: Optional[date] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    exercise: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(WorkoutSet).filter(WorkoutSet.user_id == current_user.id)
    
    if date:
        query = query.filter(WorkoutSet.workout_date == date)
    if date_from:
        query = query.filter(WorkoutSet.workout_date >= date_from)
    if date_to:
        query = query.filter(WorkoutSet.workout_date <= date_to)
    if exercise:
        query = query.filter(WorkoutSet.exercise.ilike(f"%{exercise}%"))
    
    workout_sets = query.order_by(WorkoutSet.workout_date.desc(), WorkoutSet.created_at.desc()).all()
    
    return {
        "workout_sets": [WorkoutSetResponse.from_orm(ws) for ws in workout_sets],
        "total": len(workout_sets)
    }

@app.get("/api/workouts/{workout_id}", response_model=dict, tags=["Workouts"])
async def get_workout_set(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workout_set = db.query(WorkoutSet).filter(
        WorkoutSet.id == workout_id,
        WorkoutSet.user_id == current_user.id
    ).first()
    
    if not workout_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout set not found"
        )
    
    return {"workout_set": WorkoutSetResponse.from_orm(workout_set)}

@app.put("/api/workouts/{workout_id}", response_model=dict, tags=["Workouts"])
async def update_workout_set(
    workout_id: int,
    workout_data: WorkoutSetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workout_set = db.query(WorkoutSet).filter(
        WorkoutSet.id == workout_id,
        WorkoutSet.user_id == current_user.id
    ).first()
    
    if not workout_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout set not found"
        )
    
    # Update fields if provided
    update_data = workout_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workout_set, field, value)
    
    db.commit()
    db.refresh(workout_set)
    
    return {
        "message": "Workout set updated successfully",
        "workout_set": WorkoutSetResponse.from_orm(workout_set)
    }

@app.delete("/api/workouts/{workout_id}", response_model=dict, tags=["Workouts"])
async def delete_workout_set(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workout_set = db.query(WorkoutSet).filter(
        WorkoutSet.id == workout_id,
        WorkoutSet.user_id == current_user.id
    ).first()
    
    if not workout_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout set not found"
        )
    
    db.delete(workout_set)
    db.commit()
    
    return {"message": "Workout set deleted successfully"}

@app.post("/api/workouts/{workout_id}/duplicate", response_model=dict, status_code=status.HTTP_201_CREATED, tags=["Workouts"])
async def duplicate_workout_set(
    workout_id: int,
    duplicate_data: WorkoutSetDuplicate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    original_workout = db.query(WorkoutSet).filter(
        WorkoutSet.id == workout_id,
        WorkoutSet.user_id == current_user.id
    ).first()
    
    if not original_workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout set not found"
        )
    
    # Use provided date or default to today
    new_date = duplicate_data.workout_date or date.today()
    
    duplicated_workout = WorkoutSet(
        user_id=current_user.id,
        exercise=original_workout.exercise,
        weight=original_workout.weight,
        reps=original_workout.reps,
        workout_date=new_date
    )
    
    db.add(duplicated_workout)
    db.commit()
    db.refresh(duplicated_workout)
    
    return {
        "message": "Workout set duplicated successfully",
        "workout_set": WorkoutSetResponse.from_orm(duplicated_workout)
    }

# Analytics endpoints
@app.get("/api/analytics/exercises", response_model=dict, tags=["Analytics"])
async def get_exercise_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exercises = db.query(WorkoutSet.exercise).filter(
        WorkoutSet.user_id == current_user.id
    ).distinct().order_by(WorkoutSet.exercise).all()
    
    return {"exercises": [exercise[0] for exercise in exercises]}

@app.get("/api/analytics/progress/{exercise_name}", response_model=ExerciseProgress, tags=["Analytics"])
async def get_exercise_progress(
    exercise_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get progress data grouped by date
    progress_query = db.query(
        WorkoutSet.workout_date,
        func.max(WorkoutSet.weight).label('max_weight'),
        func.avg(WorkoutSet.weight).label('avg_weight'),
        func.sum(WorkoutSet.weight * WorkoutSet.reps).label('total_volume'),
        func.count(WorkoutSet.id).label('sets')
    ).filter(
        WorkoutSet.user_id == current_user.id,
        WorkoutSet.exercise.ilike(f"%{exercise_name}%")
    ).group_by(WorkoutSet.workout_date).order_by(WorkoutSet.workout_date).all()
    
    progress_data = []
    for row in progress_query:
        progress_data.append(ProgressData(
            date=row.workout_date,
            max_weight=float(row.max_weight),
            avg_weight=float(row.avg_weight),
            total_volume=float(row.total_volume),
            sets=row.sets
        ))
    
    total_sets = sum(p.sets for p in progress_data)
    total_workouts = len(progress_data)
    
    return ExerciseProgress(
        exercise=exercise_name,
        progress_data=progress_data,
        total_workouts=total_workouts,
        total_sets=total_sets
    )

@app.get("/api/analytics/summary", response_model=WorkoutSummary, tags=["Analytics"])
async def get_workout_summary(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(WorkoutSet).filter(WorkoutSet.user_id == current_user.id)
    
    if date_from:
        query = query.filter(WorkoutSet.workout_date >= date_from)
    if date_to:
        query = query.filter(WorkoutSet.workout_date <= date_to)
    
    workout_sets = query.all()
    
    total_sets = len(workout_sets)
    total_volume = sum(ws.volume for ws in workout_sets)
    workout_days = len(set(ws.workout_date for ws in workout_sets))
    exercises = len(set(ws.exercise for ws in workout_sets))
    
    return WorkoutSummary(
        total_sets=total_sets,
        total_volume=total_volume,
        workout_days=workout_days,
        exercises=exercises,
        date_range={
            "from": date_from,
            "to": date_to
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )