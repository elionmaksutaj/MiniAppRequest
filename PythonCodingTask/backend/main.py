from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from celery.result import AsyncResult
from tasks import celery_app, create_distributed_job

app = FastAPI(
    title="Distributed Background Computation API",
    description="A demo API for distributed background processing with Celery",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobRequest(BaseModel):
    """Request model for creating a new job"""
    input_data: str
    num_chunks: int = 4
    
    class Config:
        json_schema_extra = {
            "example": {
                "input_data": "Hello world, this is a test string for distributed processing!",
                "num_chunks": 4
            }
        }


class JobResponse(BaseModel):
    """Response model for job creation"""
    job_id: str
    message: str


class JobStatusResponse(BaseModel):
    """Response model for job status"""
    job_id: str
    status: str
    progress: str | None = None
    result: dict | None = None
    error: str | None = None


@app.get("/")
def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "distributed-computation-api"}


@app.post("/jobs", response_model=JobResponse)
def create_job(request: JobRequest):
    """
    Create a new distributed computation job.
    
    The job will be split into parallel tasks and processed in the background.
    Returns a job_id that can be used to poll for status/results.
    """
    if not request.input_data:
        raise HTTPException(status_code=400, detail="input_data cannot be empty")
    
    if request.num_chunks < 1 or request.num_chunks > 10:
        raise HTTPException(status_code=400, detail="num_chunks must be between 1 and 10")
    
    # Create and dispatch the distributed job
    job = create_distributed_job(request.input_data, request.num_chunks)
    
    return JobResponse(
        job_id=job.id,
        message=f"Job created successfully. Split into {request.num_chunks} parallel tasks."
    )


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    """
    Get the status and results of a job by ID.
    
    Possible statuses:
    - PENDING: Job is waiting to be processed
    - STARTED: Job has started processing
    - SUCCESS: Job completed successfully (includes results)
    - FAILURE: Job failed (includes error message)
    """
    result = AsyncResult(job_id, app=celery_app)
    
    response = JobStatusResponse(
        job_id=job_id,
        status=result.status,
    )
    
    if result.status == "PENDING":
        response.progress = "Job is queued, waiting for worker..."
    elif result.status == "STARTED":
        response.progress = "Job is being processed..."
    elif result.status == "SUCCESS":
        response.result = result.result
    elif result.status == "FAILURE":
        response.error = str(result.result)
    
    return response


@app.get("/health")
def health_check():
    """Detailed health check including Celery connection"""
    try:
        # Check Celery broker connection
        celery_app.control.inspect().active()
        celery_status = "connected"
    except Exception as e:
        celery_status = f"error: {str(e)}"
    
    return {
        "api": "healthy",
        "celery": celery_status
    }
