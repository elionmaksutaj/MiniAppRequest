import os
import time
import random
from celery import Celery, group

# Configure Celery
celery_app = Celery(
    "tasks",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,  # Results expire after 1 hour
)


@celery_app.task(bind=True)
def process_chunk(self, chunk_id: int, data: str) -> dict:
    """
    Simulates processing a chunk of data.
    This represents one parallel subtask.
    """
    # Simulate varying processing times (1-3 seconds)
    processing_time = random.uniform(1, 3)
    time.sleep(processing_time)
    
    # Simulate some computation
    result = {
        "chunk_id": chunk_id,
        "input_length": len(data),
        "processed_chars": len(data.upper()),
        "processing_time": round(processing_time, 2),
        "status": "completed"
    }
    
    return result


@celery_app.task(bind=True)
def aggregate_results(self, results: list) -> dict:
    """
    Aggregates results from all parallel chunk tasks.
    """
    total_chars = sum(r["processed_chars"] for r in results)
    total_time = sum(r["processing_time"] for r in results)
    
    return {
        "total_chunks": len(results),
        "total_chars_processed": total_chars,
        "total_processing_time": round(total_time, 2),
        "chunk_results": results,
        "status": "completed"
    }


def create_distributed_job(input_data: str, num_chunks: int = 4):
    """
    Creates a distributed job that splits work into parallel tasks.
    Returns a chord (group of tasks + callback).
    """
    # Split input data into chunks
    chunk_size = max(1, len(input_data) // num_chunks)
    chunks = [
        input_data[i:i + chunk_size] 
        for i in range(0, len(input_data), chunk_size)
    ]
    
    # Create parallel tasks for each chunk
    parallel_tasks = group(
        process_chunk.s(idx, chunk) 
        for idx, chunk in enumerate(chunks)
    )
    
    # Chain: run parallel tasks, then aggregate results
    job = (parallel_tasks | aggregate_results.s())
    
    return job.apply_async()
