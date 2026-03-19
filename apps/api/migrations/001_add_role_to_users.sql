-- Migration: 001_add_role_to_users
-- Adds a role column to the users table with a CHECK constraint.
-- Safe to run on existing tables: DEFAULT 'student' backfills all existing rows.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'student'
        CHECK (role IN ('student', 'instructor', 'admin'));

CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);
