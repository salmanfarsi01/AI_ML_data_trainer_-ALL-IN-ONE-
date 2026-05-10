"""Configuration management for AutoML backend."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Paths ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
RESULTS_DIR = BASE_DIR / "results"
MODELS_DIR = BASE_DIR / "models"

# Create directories if they don't exist
for dir_path in [UPLOAD_DIR, RESULTS_DIR, MODELS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ─── API Configuration ────────────────────────────────────────────────────
API_TITLE = "AutoML Pipeline API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "End-to-end AutoML with AI-powered data quality auditing"

# ─── CORS Configuration ────────────────────────────────────────────────────
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:5173",
]

# ─── File Upload Configuration ────────────────────────────────────────────
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json"}

# ─── Job Configuration ────────────────────────────────────────────────────
JOB_TIMEOUT = 3600  # 1 hour in seconds
MAX_CONCURRENT_JOBS = 5

# ─── Groq Configuration ────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ─── Database Configuration ────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/automl.db")

# ─── Logging Configuration ────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / "logs" / "automl.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
