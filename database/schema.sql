-- Bible Reading Tracker Database Schema
-- Run this in your Supabase SQL editor

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id INTEGER UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'Asia/Singapore',
    current_month INTEGER DEFAULT 1,
    current_day INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Plan table (12 months × 25 days = 300 readings)
CREATE TABLE IF NOT EXISTS plan (
    id SERIAL PRIMARY KEY,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    nt1_book VARCHAR(255) NOT NULL,
    nt1_chapter VARCHAR(255) NOT NULL,
    nt2_book VARCHAR(255) NOT NULL,
    nt2_chapter VARCHAR(255) NOT NULL,
    ot1_book VARCHAR(255) NOT NULL,
    ot1_chapter VARCHAR(255) NOT NULL,
    ot2_book VARCHAR(255) NOT NULL,
    ot2_chapter VARCHAR(255) NOT NULL,
    UNIQUE(month, day)
);

-- User progress table
CREATE TABLE IF NOT EXISTS user_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User events table (read, break, nudge)
CREATE TABLE IF NOT EXISTS user_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'read', 'break', 'nudge'
    month INTEGER,
    day INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Processed callbacks table (for idempotency)
CREATE TABLE IF NOT EXISTS processed_callbacks (
    id SERIAL PRIMARY KEY,
    callback_id VARCHAR(255) UNIQUE NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_plan_month_day ON plan(month, day);
CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_progress_completed_at ON user_progress(completed_at);
CREATE INDEX IF NOT EXISTS idx_user_events_user_id ON user_events(user_id);
CREATE INDEX IF NOT EXISTS idx_user_events_event_type ON user_events(event_type);
CREATE INDEX IF NOT EXISTS idx_user_events_created_at ON user_events(created_at);
CREATE INDEX IF NOT EXISTS idx_processed_callbacks_callback_id ON processed_callbacks(callback_id);
