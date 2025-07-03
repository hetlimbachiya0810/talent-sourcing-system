# Talent Sourcing System

A system to manage job descriptions, candidate CVs, and automate candidate matching.

## Backend Setup
1. Install PostgreSQL and create a database: `psql -U postgres -c "CREATE DATABASE talent_sourcing;"`.
2. Create `.env` in the root with `DATABASE_URL=postgresql://user:password@localhost:5432/talent_sourcing`.
3. Install backend dependencies: `cd backend && pip install -r requirements.txt`.
4. Initialize database: `cd backend && python init_db.py`.

## Project Structure
- `backend/models/models.py`: Database schema for Job, Vendor, Candidate.
- `backend/db/database.py`: Database connection and session setup.
- `backend/init_db.py`: Script to create database tables.
- `backend/main.py`: FastAPI app (to be used in later tasks).