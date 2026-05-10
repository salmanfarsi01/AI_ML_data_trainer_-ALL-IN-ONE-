# AutoML Backend - Complete File Structure

## 📋 File Manifest

### Core Application Files

**main.py** (1300+ lines)
- FastAPI application with all endpoints
- Health checks and info endpoints
- File upload handling
- Pipeline orchestration (profile, audit, preprocess, train, run)
- Job management endpoints
- Prediction endpoints
- Error handling and logging
- CORS middleware setup

**config.py**
- Environment configuration
- Path management (uploads, models, results, logs)
- API settings
- CORS allowed origins
- File upload limits
- Job timeout configuration
- Groq API setup

**schemas.py**
- Pydantic models for all request/response types
- Enumerations (TaskType, SeverityLevel, IssueType)
- 15+ data models for type validation
- Automatic validation and OpenAPI documentation

**job_manager.py**
- Async job tracking system
- Job lifecycle management (pending → running → completed/failed)
- Progress monitoring
- Concurrent job limiting with semaphores
- Timeout handling
- Automatic cleanup of old jobs
- Global job_manager instance

**utils.py**
- File handling utilities
- Model serialization/deserialization (pickle)
- Results persistence (JSON)
- Data format conversion
- Dataset validation
- Schema conversion functions
- Available models detection

### Integration Files

**auto_ai.py** (Existing - Enhanced)
- Refactored for API integration
- All 8 pipeline stages exposed
- Train/Test/CV generalization tracking
- Overfitting/underfitting detection
- Export-ready function signatures

### Configuration Files

**.env.example**
- Template for environment variables
- GROQ_API_KEY placeholder
- Database, logging, server config
- Job management settings
- File upload limits

**.env** (git-ignored)
- Your actual environment variables
- Should be created from .env.example
- Contains sensitive keys (not tracked)

**requirements.txt**
- All Python dependencies listed
- Pinned versions for reproducibility
- Includes FastAPI, data science, and async libraries
- 20+ packages configured

### Documentation Files

**BACKEND_README.md**
- Complete backend documentation
- Quick start guide
- API endpoint reference
- Usage examples
- Configuration guide
- Troubleshooting section
- Performance tips

**INTEGRATION_SUMMARY.md**
- Architecture overview
- Project structure diagram
- Feature inventory
- Data flow documentation
- Security features
- Scalability features
- Getting started steps

**API_EXAMPLES.sh**
- 12 main endpoint examples
- 5 advanced usage patterns
- cURL command templates
- Data export examples
- Continuous monitoring script

**QUICKSTART_GUIDE.md** (This file)
- Project file structure
- What each file does
- How files work together
- Key features
- Getting started

### Setup/Deployment Files

**quickstart.sh** (Linux/Mac)
- Bash setup script
- Environment validation
- Dependency installation
- Server startup instructions

**quickstart.bat** (Windows)
- Batch setup script
- Python validation
- Dependency installation
- Server startup instructions

**Dockerfile**
- Docker container definition
- Python 3.11 slim base
- Dependency installation
- Health check setup
- Volume mount configuration

**docker-compose.yml**
- Docker Compose orchestration
- Service definition
- Environment variable injection
- Volume persistence
- Port mapping
- Health check configuration

### Testing Files

**test_api.py**
- Comprehensive test suite
- Health and info tests
- File upload simulation
- Profiling test
- Audit test (with Groq)
- Job status test
- Async operations examples

### Data Directories (Auto-created)

**uploads/**
- Temporary storage for uploaded files
- Dataset files from users
- Preview data caching

**models/**
- Trained model storage
- Organized by job_id
- Pickled model files
- Model versioning support

**results/**
- Pipeline results JSON
- Organized by job_id
- Audit flags
- Training metrics
- Evaluation results

**logs/**
- Application logs
- Request/response logs
- Error tracking
- Performance monitoring

## 🔗 File Relationships

```
main.py (FastAPI App)
  ├─ schemas.py (Request/Response validation)
  ├─ job_manager.py (Async job tracking)
  ├─ utils.py (Helper functions)
  │   ├─ config.py (Settings)
  │   └─ auto_ai.py (Pipeline logic)
  ├─ config.py (Paths, Settings)
  └─ auto_ai.py (ML Pipeline)
      ├─ auto_ai.build_profile()
      ├─ auto_ai.run_ai_audit() → Groq API
      ├─ auto_ai.apply_preprocessing()
      ├─ auto_ai.run_feature_engineering()
      ├─ auto_ai.train_models()
      └─ auto_ai.evaluate_all()
```

## 🚀 Getting Started with Files

### 1. Setup Phase
- Copy `.env.example` → `.env`
- Edit `.env` with your GROQ_API_KEY
- Run `quickstart.sh` or `quickstart.bat`

### 2. Start Server
- `uvicorn main:app --reload`
- Or use Docker: `docker-compose up`

### 3. Verify Installation
- Check `http://localhost:8000/health`
- Access `http://localhost:8000/docs` (Swagger)

### 4. Test API
- Run `python test_api.py`
- Or use cURL from `API_EXAMPLES.sh`

### 5. Deploy
- Use `Dockerfile` for containerization
- Or `docker-compose.yml` for full stack

## 📦 File Sizes

| File | Size | Purpose |
|------|------|---------|
| main.py | ~8KB | FastAPI application |
| schemas.py | ~6KB | Data models |
| job_manager.py | ~4KB | Job management |
| utils.py | ~4KB | Utilities |
| config.py | ~2KB | Configuration |
| test_api.py | ~4KB | Test suite |
| Dockerfile | ~1KB | Container definition |
| docker-compose.yml | ~1KB | Orchestration |
| BACKEND_README.md | ~10KB | Documentation |
| INTEGRATION_SUMMARY.md | ~8KB | Architecture |
| API_EXAMPLES.sh | ~6KB | Usage examples |

## 🔧 Configuration Files Map

```
Environment (.env)
├─ API Configuration
│  ├─ GROQ_API_KEY → AI audit service
│  ├─ GROQ_MODEL → LLM model selection
│  └─ LOG_LEVEL → Logging verbosity
├─ Server Configuration
│  ├─ HOST → Bind address
│  └─ PORT → Listen port
├─ File Configuration
│  └─ MAX_UPLOAD_SIZE_MB → Upload limit
├─ Job Configuration
│  ├─ JOB_TIMEOUT_SECONDS → Max job duration
│  └─ MAX_CONCURRENT_JOBS → Parallel limit
└─ Database Configuration
   └─ DATABASE_URL → Storage location
```

## 📊 Data Flow Through Files

```
1. User uploads file
   ↓ test_api.py or HTTP request
   ↓ main.py: /upload endpoint
   ↓ utils.py: save_uploaded_file()
   ↓ uploads/ directory

2. Run audit
   ↓ main.py: /pipeline/audit
   ↓ auto_ai.py: build_profile() + run_ai_audit()
   ↓ Groq API (external)
   ↓ utils.py: convert_flags_to_schema()
   ↓ schemas.py: AuditResponse

3. Full pipeline
   ↓ main.py: /pipeline/run (creates job)
   ↓ job_manager.py: tracks progress
   ↓ auto_ai.py: all 8 stages
   ↓ utils.py: save_model(), save_results()
   ↓ models/ and results/ directories
   ↓ schemas.py: TrainingResponse

4. Make prediction
   ↓ main.py: /predict endpoint
   ↓ utils.py: load_model()
   ↓ models/ directory
   ↓ schemas.py: PredictionResponse
```

## ✅ All Features Covered

✓ File upload with validation
✓ Dataset profiling
✓ AI-powered audit
✓ Automated preprocessing
✓ Feature engineering
✓ Multi-model training
✓ Comprehensive evaluation
✓ Overfitting detection
✓ Model persistence
✓ Job management
✓ Prediction serving
✓ Async processing
✓ Error handling
✓ Logging
✓ Docker support
✓ Documentation
✓ Examples
✓ Testing

## 🎯 Next Steps

1. Read `BACKEND_README.md` for detailed usage
2. Review `INTEGRATION_SUMMARY.md` for architecture
3. Check `API_EXAMPLES.sh` for endpoint examples
4. Run `test_api.py` to verify setup
5. Use Swagger UI (`/docs`) for interactive testing
6. Deploy with Docker if needed

## 📞 Support Resources

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI**: http://localhost:8000/openapi.json
- **README**: BACKEND_README.md
- **Examples**: API_EXAMPLES.sh
- **Tests**: test_api.py
- **Architecture**: INTEGRATION_SUMMARY.md
