-- PostgreSQL Database Initialization Script
-- This script runs when the PostgreSQL container starts for the first time

-- Create test database for running tests
CREATE DATABASE rental_test_db;

-- Grant permissions to the rental_user for the test database
GRANT ALL PRIVILEGES ON DATABASE rental_test_db TO rental_user;

-- Enable useful extensions for both databases
\c rental_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

\c rental_test_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create indexes for better performance (will be created by Alembic, but good to have)
-- These are commonly used patterns in the rental system

-- Note: Actual table creation will be handled by Alembic migrations
-- This script just sets up the database structure and extensions