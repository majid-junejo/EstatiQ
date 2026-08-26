import subprocess
import sys
import time

print("Starting Backend (FastAPI on port 8000)...")
backend_process = subprocess.Popen([sys.executable, "file.py"])

time.sleep(3)

print("Starting Frontend (Streamlit on port 8501)...")
frontend_process = subprocess.Popen([
    sys.executable, "-m", "streamlit", "run", "frontend.py",
    "--server.port", "8501",
    "--server.headless", "true"
])

print("Both EstatiQ services are running!")

try:
    backend_process.wait()
    frontend_process.wait()
except KeyboardInterrupt:
    backend_process.terminate()
    frontend_process.terminate()
