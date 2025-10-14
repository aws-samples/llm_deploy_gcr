#!/usr/bin/env python3
"""
FastAPI high-concurrency SageMaker endpoint server startup script
"""
import uvicorn
import multiprocessing

if __name__ == '__main__':
    # Get CPU core count
    cpu_count = multiprocessing.cpu_count()
    worker_count = min(cpu_count, 4)  # Limit maximum process count
    
    print(f"Starting FastAPI server with {worker_count} workers...")
    
    # Start with uvicorn, automatic high concurrency support
    uvicorn.run(
        "endpoint:app",
        host="0.0.0.0",
        port=8080,
        workers=worker_count,
        access_log=False,
        loop="uvloop"
    )