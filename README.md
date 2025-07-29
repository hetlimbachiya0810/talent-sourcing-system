# Talent Sourcing System

A comprehensive system to manage job descriptions, vendor relationships, candidate CVs, and automate intelligent candidate-job matching using advanced text parsing and fuzzy matching algorithms.

## 🚀 Features

### Core Functionality
- **Job Management**: Create, update, and manage job descriptions with detailed requirements
- **Vendor Management**: Track and manage vendor relationships and submissions
- **Candidate Management**: Handle candidate profiles with CV uploads and detailed information
- **File Upload**: Support for PDF and DOCX CV uploads via Cloudinary integration

### Advanced Matching Engine
- **Intelligent CV-JD Matching**: Automated matching between candidate CVs and job descriptions
- **Multi-criteria Scoring**: Evaluates candidates on:
  - Hard Skills (40% weight)
  - Soft Skills (20% weight)
  - Certifications (20% weight)
  - Time Zone Alignment (10% weight)
  - Contract Duration Compatibility (10% weight)
- **Fuzzy Text Matching**: Advanced text similarity algorithms for flexible keyword matching
- **Automated Status Assignment**: Candidates automatically marked as "Shortlisted" (≥80% match) or "Rejected"
- **Mismatch Analysis**: Detailed summaries of missing skills and requirements for rejected candidates

### API Endpoints
- **Jobs**: CRUD operations for job management
- **Vendors**: Vendor registration and management
- **Candidates**: Candidate submission with automatic matching
- **Matching**: Dedicated endpoints for processing and retrieving match results

## 📁 Project Structure

```
talent-sourcing-system/
├── backend/
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py              # Database connection and session management
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py                # SQLAlchemy models (Job, Vendor, Candidate)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── jobs.py                  # Job management endpoints
│   │   ├── vendors.py               # Vendor management endpoints
│   │   └── candidates.py            # Candidate and matching endpoints
│   ├── services/
│   │   └── matching_service.py      # Core matching orchestration service
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── text_parser.py           # CV/JD text extraction utilities
│   │   └── matching_engine.py       # Intelligent matching algorithms
│   ├── init_db.py                   # Database initialization script
│   ├── main.py                      # FastAPI application entry point
│   ├── schemas.py                   # Pydantic schemas for API validation
│   ├── requirements.txt             # Python dependencies
│   ├── test_matching_script.py      # Comprehensive matching engine test
│   └── test_schemas.py              # Database schema validation test
├── frontend/
│   ├── public/
│   │   └── index.html               # Basic HTML template
│   ├── src/
│   │   └── App.js                   # React application entry point
│   └── package.json                 # Frontend dependencies
├── .env                             # Environment variables (create manually)
├── .gitignore                       # Git ignore patterns
├── .vscode/settings.json            # VS Code configuration
└── README.md                        # This file
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8 or higher
- PostgreSQL database
- Node.js and npm (for frontend)
- Cloudinary account (for file uploads)

### Backend Setup

1. **Install PostgreSQL and create database:**
   ```bash
   # Using psql command line
   psql -U postgres -c "CREATE DATABASE talent_sourcing;"
   
   # Or using PostgreSQL GUI tools like pgAdmin
   ```

2. **Environment Configuration:**
   Create a `.env` file in the project root:
   ```env
   # Database Configuration
   DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/talent_sourcing
   
   # Cloudinary Configuration (for CV uploads)
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   # Alternative: Use single URL format
   # CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
   ```

3. **Install Backend Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Initialize Database:**
   ```bash
   cd backend
   python init_db.py
   ```

5. **Start the Backend Server:**
   ```bash
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at: `http://localhost:8000`
   API Documentation: `http://localhost:8000/docs`

### Frontend Setup (Basic)

1. **Install Frontend Dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start Frontend Development Server:**
   ```bash
   cd frontend
   npm start
   ```

   The frontend will be available at: `http://localhost:3000`

## 🧪 Testing the System

### Test the Matching Engine

Run the comprehensive test script to validate the matching functionality:

```bash
cd backend
python test_matching_script.py
```

This script will:
- Create sample job, vendor, and candidate data
- Process automatic CV-JD matching
- Display detailed match scores and analysis
- Test all matching-related API functionalities

### Test Database Schema

Validate the database models and relationships:

```bash
cd backend
python test_schemas.py
```

## 📚 API Documentation

### Key Endpoints

#### Jobs
- `POST /jobs/` - Create new job
- `GET /jobs/` - List all jobs
- `GET /jobs/{job_id}` - Get specific job
- `PATCH /jobs/{job_id}` - Update job

#### Vendors
- `POST /vendors/` - Create new vendor
- `GET /vendors/` - List all vendors

#### Candidates & Matching
- `POST /candidates/` - Submit candidate with CV (triggers automatic matching)
- `GET /candidates/` - List all candidates
- `GET /candidates/by-job/{job_id}` - Get candidates for specific job
- `GET /candidates/by-vendor/{vendor_id}` - Get candidates from specific vendor
- `POST /candidates/match/{candidate_id}` - Process matching for specific candidate
- `POST /candidates/match-job/{job_id}` - Process matching for all job candidates
- `GET /candidates/match-results/{job_id}` - Get match results for job
- `GET /candidates/shortlisted/{job_id}` - Get shortlisted candidates only

### Sample API Usage

#### Create a Job
```bash
curl -X POST "http://localhost:8000/jobs/" \
-H "Content-Type: application/json" \
-d '{
  "title": "Senior Python Developer",
  "description": "Looking for experienced Python developer with FastAPI and AWS skills",
  "time_zone": "IST",
  "budget_range": "$50-70/hour",
  "contract_duration": "6 months"
}'
```

#### Submit a Candidate
```bash
curl -X POST "http://localhost:8000/candidates/" \
-F "cv_file=@candidate_cv.pdf" \
-F "job_id=1" \
-F "vendor_id=1" \
-F "name=John Doe" \
-F "email=john@example.com" \
-F "hard_skills=Python, FastAPI, AWS, Docker" \
-F "soft_skills=Communication, Leadership" \
-F "experience=5" \
-F "time_zone_alignment=IST" \
-F "contract_duration_willingness=6 months"
```

## 🔧 Technical Details

### Matching Algorithm
The system uses a sophisticated multi-criteria matching approach:

1. **Text Extraction**: Extracts text from uploaded CV files (PDF/DOCX)
2. **Keyword Identification**: Identifies relevant keywords using predefined skill databases
3. **Fuzzy Matching**: Uses Levenshtein distance and partial ratio matching for flexible comparisons
4. **Weighted Scoring**: Combines multiple criteria with configurable weights
5. **Threshold-based Classification**: Automatically categorizes candidates as shortlisted or rejected

### Technology Stack
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **File Processing**: PyMuPDF (PDF), python-docx (Word documents)
- **Text Matching**: FuzzyWuzzy with Levenshtein distance
- **File Storage**: Cloudinary for CV uploads
- **Frontend**: React (basic setup)

### Database Schema
- **Jobs**: Store job requirements and descriptions
- **Vendors**: Manage vendor relationships
- **Candidates**: Store candidate profiles with matching results
- **Relationships**: Foreign key relationships between jobs, vendors, and candidates

## 🔮 Future Enhancements

- Enhanced UI/UX with comprehensive React frontend
- Machine learning-based matching improvements
- Email notifications for new matches
- Advanced reporting and analytics
- Bulk candidate processing
- Integration with job boards and ATS systems
- Role-based access control and authentication

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

For questions or support, please open an issue in the project repository.