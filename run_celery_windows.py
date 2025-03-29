"""
Windows-compatible script to run Celery worker and beat.
This avoids issues with the default Celery worker on Windows.
"""

import os
import sys
import time
import signal
import threading
import subprocess
from celery._state import get_current_app

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Import necessary modules
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from myproject.celery import app as celery_app

def terminate_process():
    """Terminate this script and all child processes."""
    print("\nTerminating Celery worker and beat...")
    os.kill(os.getpid(), signal.SIGTERM)

def run_celery_worker():
    """Start Celery worker using the solo pool (better for Windows)."""
    print("Starting Celery worker...")
    cmd = [
        sys.executable, "-m", 
        "celery", "-A", "myproject", "worker",
        "--pool=solo", "--loglevel=info",
        "--without-gossip", "--without-mingle", 
    ]
    
    worker_process = subprocess.Popen(cmd)
    print(f"Celery worker started with PID: {worker_process.pid}")
    return worker_process

def run_celery_beat():
    """Start Celery beat for scheduled tasks."""
    print("Starting Celery beat...")
    cmd = [
        sys.executable, "-m", 
        "celery", "-A", "myproject", "beat",
        "--loglevel=info",
    ]
    
    beat_process = subprocess.Popen(cmd)
    print(f"Celery beat started with PID: {beat_process.pid}")
    return beat_process

def manual_run_disaster_check():
    """Run the disaster check task directly via code."""
    from users.tasks import check_disaster_predictions
    
    print("\nManually running disaster check task...")
    result = check_disaster_predictions.delay()
    print(f"Task ID: {result.id}, Status: {result.status}")
    return result

if __name__ == "__main__":
    print("=== Starting Celery processes for Disaster Prediction System ===")
    print("Press Ctrl+C to stop all processes")
    
    # Start worker and beat in separate processes
    worker_process = run_celery_worker()
    time.sleep(3)  # Wait for worker to initialize
    beat_process = run_celery_beat()
    
    # Register signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutting down Celery processes...")
        beat_process.terminate()
        worker_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Wait a bit, then manually run the check task once
    try:
        time.sleep(10)
        result = manual_run_disaster_check()
        
        # Keep the main thread alive
        while True:
            time.sleep(10)
            print("Celery processes running... (Press Ctrl+C to stop)")
    except KeyboardInterrupt:
        signal_handler(None, None) 