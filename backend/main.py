from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.jobs import router as jobs_router

app = FastAPI(
    title="Talent Sourcing System API",
    description="API for managing job descriptions, vendors, and candidate matching",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs_router)

@app.get("/")
async def read_root():
    return {"message": "Talent Sourcing System API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}