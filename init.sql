-- Workout Tracker Database Schema
-- PostgreSQL initialization script

-- Drop existing tables if they exist (for clean reinstalls)
DROP TABLE IF EXISTS workout_sets CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
);

-- Create workout_sets table
CREATE TABLE workout_sets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    exercise VARCHAR(255) NOT NULL,
    weight DECIMAL(10,2) NOT NULL,
    reps INTEGER NOT NULL,
    workout_date DATE NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
    CONSTRAINT fk_workout_sets_user_id 
        FOREIGN KEY (user_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_workout_sets_user_id ON workout_sets(user_id);
CREATE INDEX idx_workout_sets_workout_date ON workout_sets(workout_date);
CREATE INDEX idx_workout_sets_exercise ON workout_sets(exercise);
CREATE INDEX idx_workout_sets_user_exercise ON workout_sets(user_id, exercise);
CREATE INDEX idx_workout_sets_user_date ON workout_sets(user_id, workout_date);

-- Optional: Create a view for workout sets with calculated volume
CREATE VIEW workout_sets_with_volume AS
SELECT 
    id,
    user_id,
    exercise,
    weight,
    reps,
    workout_date,
    created_at,
    (weight * reps) AS volume
FROM workout_sets;

-- Optional: Insert some sample data for testing (remove in production)
-- Uncomment the following lines if you want sample data

/*
-- Sample user
INSERT INTO users (username, email, password_hash) VALUES 
('testuser', 'test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeVF7CQRo5wCAhfHy'); -- password: "testpass123"

-- Sample workout sets
INSERT INTO workout_sets (user_id, exercise, weight, reps, workout_date) VALUES 
(1, 'Bench Press', 135.0, 10, '2025-01-01'),
(1, 'Squat', 185.0, 8, '2025-01-01'),
(1, 'Deadlift', 225.0, 5, '2025-01-01'),
(1, 'Bench Press', 140.0, 8, '2025-01-03'),
(1, 'Squat', 190.0, 8, '2025-01-03'),
(1, 'Overhead Press', 95.0, 10, '2025-01-03');
*/

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;