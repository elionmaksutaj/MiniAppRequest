# MiniAppRequest

# Distributed Background Computation Demo

A mini full-stack application demonstrating distributed background computation using **FastAPI**, **Celery**, **Redis**, and a simple **HTML/CSS/JS frontend**, orchestrated with **Docker Compose**.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [API Endpoints](#api-endpoints)
- [How It Works](#how-it-works)
- [Frontend Features](#frontend-features)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Conceptual Questions](#conceptual-questions)
- [License](#license)

---

## Overview

This application demonstrates a common pattern in distributed systems: **offloading long-running tasks to background workers**. Instead of blocking the user while processing, the system:

1. Accepts a job request and returns immediately with a job ID
2. Processes the job asynchronously in the background using parallel workers
3. Allows the client to poll for job status and retrieve results when complete

**Use Cases:** Video processing, report generation, data pipelines, bulk email sending, image manipulation, etc.

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│    Frontend     │────▶│    FastAPI      │────▶│     Redis       │
│   (Nginx:3000)  │     │  (Backend:8000) │     │   (Broker:6379) │
│                 │◀────│                 │◀────│                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │                 │
                                                │  Celery Worker  │
                                                │  (Background)   │
                                                │                 │
                                                └─────────────────┘
```

### Data Flow

1. **User submits job** via frontend form
2. **FastAPI** receives request, creates Celery task, returns `job_id`
3. **Celery** picks up task from Redis queue, splits into parallel subtasks
4. **Frontend polls** `/jobs/{job_id}` endpoint for status updates
5. **Results displayed** when all subtasks complete

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend API | FastAPI | REST API endpoints, request validation |
| Task Queue | Celery | Distributed task execution |
| Message Broker | Redis | Message passing between API and workers |
| Result Backend | Redis | Storing task results |
| Frontend | HTML/CSS/JS | User interface |
| Web Server | Nginx | Serving static files, reverse proxy |
| Containerization | Docker Compose | Service orchestration |

---

## Project Structure

```
project/
├── docker-compose.yml          # Service orchestration
├── README.md                   # This file
│
├── backend/
│   ├── Dockerfile              # Python container configuration
│   ├── requirements.txt        # Python dependencies
│   ├── main.py                 # FastAPI application & endpoints
│   └── tasks.py                # Celery task definitions
│
└── frontend/
    ├── Dockerfile              # Nginx container configuration
    ├── nginx.conf              # Nginx configuration with API proxy
    ├── index.html              # Main HTML page
    ├── styles.css              # Styling
    └── script.js               # Frontend logic (form handling, polling)
```

---

## Prerequisites

- **Docker Desktop** (includes Docker Engine and Docker Compose)
  - [Download for Windows/Mac](https://www.docker.com/products/docker-desktop)
  - Linux: Install via package manager

Verify installation:

```bash
docker --version
docker compose version
```

---

## Getting Started

### 1. Clone or Download the Project

```bash
# If using git
git clone <repository-url>
cd <project-folder>

# Or extract the downloaded ZIP file
```

### 2. Build and Start Services

```bash
docker compose up --build
```

Wait for all services to start. You should see:

```
backend-1        | INFO:     Uvicorn running on http://0.0.0.0:8000
celery_worker-1  | celery@xxxxx ready.
frontend-1       | ... nginx ...
```

### 3. Access the Application

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Main user interface |
| Backend API | http://localhost:8000 | REST API |
| API Documentation | http://localhost:8000/docs | Swagger UI |
| Alternative Docs | http://localhost:8000/redoc | ReDoc UI |

### 4. Stop the Application

```bash
# Press Ctrl+C to stop, then:
docker compose down

# To also remove volumes (clears Redis data):
docker compose down -v
```

---

## API Endpoints

### Health Check

```
GET /
```

Returns API status and available endpoints.

### Submit a Job

```
POST /jobs
Content-Type: application/json

{
  "data": "Your text data to process",
  "num_chunks": 4
}
```

**Response:**

```json
{
  "job_id": "abc123-def456-...",
  "status": "submitted",
  "message": "Job submitted successfully. Poll /jobs/{job_id} for status."
}
```

### Get Job Status

```
GET /jobs/{job_id}
```

**Response (In Progress):**

```json
{
  "job_id": "abc123-def456-...",
  "status": "STARTED",
  "progress": {
    "completed": 2,
    "total": 4,
    "percentage": 50
  }
}
```

**Response (Complete):**

```json
{
  "job_id": "abc123-def456-...",
  "status": "SUCCESS",
  "result": {
    "original_data": "Your text data",
    "num_chunks": 4,
    "chunk_results": [...],
    "processing_time": 2.45,
    "total_characters_processed": 120
  }
}
```

### List All Jobs

```
GET /jobs
```

Returns a list of all tracked jobs with their current status.

---

## How It Works

### The Computation Flow

1. **Job Submission**: User submits text data with desired number of parallel chunks

2. **Task Creation**: FastAPI creates a Celery `chord`:
   - A `chord` is a group of parallel tasks followed by a callback
   - The input data is split into N chunks
   - Each chunk is processed by a separate `process_chunk` task

3. **Parallel Processing**: Each `process_chunk` task:
   - Simulates work with a random delay (1-3 seconds)
   - Performs character analysis on its chunk
   - Returns results independently

4. **Result Aggregation**: When all chunks complete, the `aggregate_results` callback:
   - Collects all chunk results
   - Computes summary statistics
   - Stores final result in Redis

5. **Polling**: Frontend polls every 1.5 seconds until status is `SUCCESS` or `FAILURE`

### Celery Task Types Used

| Task Type | Purpose |
|-----------|---------|
| `@shared_task` | Individual chunk processing |
| `chord` | Parallel execution with callback |
| `group` | Parallel task group |

---

## Frontend Features

- **Job Submission Form**: Input text data and select number of parallel chunks (1-10)
- **Real-time Status Updates**: Automatic polling with progress percentage
- **Visual Progress Indicator**: Animated progress bar
- **Result Display**: Formatted JSON results with processing statistics
- **Job History**: View previously submitted jobs
- **Responsive Design**: Works on desktop and mobile

---

## Configuration

### Environment Variables

Defined in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Redis connection for task queue |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/0` | Redis connection for results |

### Scaling Workers

To run multiple Celery workers for higher throughput:

```bash
docker compose up --scale celery_worker=3
```

### Ports

| Service  | Internal Port | External Port |
|----------|---------------|---------------|
| Frontend | 80    | 3000 |
| Backend  | 8000  | 8000 |
| Redis    | 6379  | 6379 |

---

## Troubleshooting

### Build Fails with pip Error

```bash
# Clean up and rebuild
docker compose down
docker system prune -f
docker compose up --build
```

### Port Already in Use

```bash
# Check what's using the port
# Windows:
netstat -ano | findstr :3000

# Mac/Linux:
lsof -i :3000

# Change ports in docker-compose.yml if needed
```

### Celery Worker Not Processing Tasks

```bash
# Check worker logs
docker compose logs celery_worker

# Restart workers
docker compose restart celery_worker
```

### Redis Connection Issues

```bash
# Ensure Redis is running
docker compose ps

# Check Redis logs
docker compose logs redis
```

### View All Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
```

---

## Development

### Rebuilding After Code Changes

```bash
# Backend changes
docker compose up --build backend celery_worker

# Frontend changes
docker compose up --build frontend

# All services
docker compose up --build
```

### Accessing Container Shell

```bash
# Backend container
docker compose exec backend /bin/bash

# Redis CLI
docker compose exec redis redis-cli
```

---

## Conceptual Questions

### Question 1: Complexity & Algorithm Efficiency

**Q: What do Big-O, Big-$\Theta$, and Big-$\Omega$ describe, and how would you compare $O(n \log n)$ vs $O(n^2)$ in practice?**

A: These describe the efficiency bounds of an algorithm as the input size ($n$) grows. Big-O ($O$) is the upper bound (worst-case), Big-$\Omega$ ($\Omega$) is the lower bound (best-case), and Big-$\Theta$ ($\Theta$) is the tight bound (average).

In practice: An $O(n \log n)$ algorithm (like Merge Sort) is drastically more efficient than an $O(n^2)$ algorithm (like Bubble Sort). For a dataset of 10,000 items, $O(n^2)$ requires 100,000,000 operations, while $O(n \log n)$ requires only ~130,000.

---

### Question 2: Choosing the Right Data Structure

**Q: When would you choose an array/list, linked list, hash map, or tree? Give one trade-off for each.**

A: Array/List: Best for fast index-based access. Trade-off: Slow to insert/delete in the middle ($O(n)$).

Linked List: Best for frequent insertions at the ends. Trade-off: No random access; must traverse the list.

Hash Map: Best for $O(1)$ lookups via keys. Trade-off: Uses more memory to prevent collisions.

Tree: Best for hierarchical data or sorted retrieval. Trade-off: Slower lookup ($O(\log n)$) than a hash map.

---

### Question 3: Immutability & Concurrency

**Q: What’s the difference between mutable and immutable data? Why can immutability simplify reasoning and concurrency?**

A: Mutable data (like Python lists) can be changed after creation, while immutable data (like Python tuples) cannot. Immutability simplifies reasoning because the state of an object is guaranteed not to change unexpectedly. In concurrency, it eliminates race conditions since multiple threads can safely read the same data without needing complex locks to prevent writes.

---

### Question 4: Memory Model: Stack vs. Heap

**Q: What’s the difference between the stack and the heap? How do scope and lifetime relate to each?**

A: The Stack is fast, structured memory for local variables and function calls, managed in a LIFO order. The Heap is a large, flexible pool for dynamic object allocation.

Scope/Lifetime: Stack memory is tied to scope (it’s cleared when the function ends). Heap memory has a lifetime that lasts until it is explicitly freed or garbage collected.

---

### Question 5: OOP Fundamentals

**Q: Explain encapsulation, inheritance, and polymorphism. When is composition preferable to inheritance?**

A: Encapsulation: Hiding internal data and only exposing it via methods.

Inheritance: Letting a class adopt the properties of a parent class.

Polymorphism: Using a single interface to represent different underlying forms.

Composition is preferable when you want to build flexible objects by combining behaviors ("has-a") rather than creating rigid hierarchies ("is-a").

---

### Question 6: APIs & Idempotency

**Q: What is an idempotent API operation? Give an example of an idempotent vs non-idempotent HTTP method.**

A: An operation is idempotent if performing it multiple times produces the same result as performing it once.

Idempotent: GET (fetching data) or PUT (setting a state).

Non-idempotent: POST (calling it twice usually creates two separate records).

---

### Question 7: Concurrency vs. Parallelism

**Q: Define both. What problems do race conditions and deadlocks cause, and how can you mitigate them?**

A: Concurrency is managing multiple tasks at once (interleaving), whereas Parallelism is doing multiple things at the same time (multi-core).

Problems: Race conditions cause unpredictable data; Deadlocks cause the program to freeze.

Mitigation: Use locks (mutexes), semaphores, or design with immutable data structures.

---

### Question 8: Databases: SQL vs. NoSQL

**Q:When would you pick SQL vs NoSQL? What are indexes and how can they both help and hurt performance?**

A: Pick SQL for structured data and ACID compliance. Pick NoSQL for unstructured data and massive scale. Indexes are data structures that help by making queries faster but hurt by slowing down write operations (as the index must be updated every time).

---

### Question 9: The Testing Pyramid

**Q: Contrast unit, integration, and end-to-end tests. When should you mock, and what are the risks of over-mocking?**

A: Unit tests check small pieces; 

Integration tests check how modules interact; 

End-to-End tests check the entire user flow. 

Use mocking to replace slow or unstable external dependencies (like APIs). The risk of over-mocking is that your tests might pass, but you aren't testing the actual behavior of the real system.

---

### Question 10: Merge vs. Rebase

**Q: Explain the differences between merge and rebase in Git. When would you favor one over the other?**

A: Merge creates a new commit that joins the history of two branches. Rebase moves your branch's commits to the tip of the target branch for a linear history.

Favor Rebase: For local cleanup to keep a clean, readable history before sharing.

Favor Merge: For public/shared branches to avoid breaking other people's history.

---

## License

This project is provided as a coding exercise demonstration. Feel free to use and modify for learning purposes.
