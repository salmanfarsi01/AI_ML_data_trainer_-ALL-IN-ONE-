# Complete Integration Guide - AutoML Frontend & Backend

## 🎯 Project Overview

This is a complete end-to-end AutoML application with:
- **Backend**: FastAPI server with ML pipeline
- **Frontend**: React UI for interactive use

```
AutoML Application
├── Backend (Python/FastAPI)
│   ├── auto_ai.py - AutoML pipeline logic
│   ├── main.py - REST API server
│   └── Supporting services
│
└── Frontend (React/JavaScript)
    ├── Upload interface
    ├── Pipeline visualization
    └── Results display
```

## 🚀 Getting Started - Complete Setup

### Step 1: Backend Setup

```bash
# Navigate to backend directory
cd automl-backend

# Create environment file
cp .env.example .env

# Add your GROQ_API_KEY to .env
# (Get it from https://console.groq.com)

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn main:app --reload
```

Backend will be available at: **http://localhost:8000**

Access API documentation at: **http://localhost:8000/docs**

### Step 2: Frontend Setup

```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:3000**

## 📊 User Workflow

### Using the Application

1. **Open Frontend**: Navigate to http://localhost:3000
2. **Upload Dataset**: 
   - Click upload area
   - Select CSV/Excel file
   - Enter target column name
   - Click "Upload & Analyze"
3. **Watch Pipeline**:
   - See real-time progress through 6 stages
   - Monitor each step's status
   - Track overall completion percentage
4. **View Results**:
   - See model performance metrics
   - Review data quality flags
   - Check generalization status

## 🔄 Data Flow

```
User Interface
    ↓
[Upload File] → Frontend validates → Backend /upload
    ↓
[Profile Data] → auto_ai.build_profile()
    ↓
[AI Audit] → auto_ai.run_ai_audit() → Groq API
    ↓
[Preprocess] → auto_ai.apply_preprocessing()
    ↓
[Features] → auto_ai.run_feature_engineering()
    ↓
[Train] → auto_ai.train_models()
    ↓
[Evaluate] → auto_ai.evaluate_all()
    ↓
Results saved → Frontend displays results
```

## 📁 File Structure

```
automated_ml/
├── automl-backend/           # FastAPI server
│   ├── main.py              # REST API endpoints
│   ├── auto_ai.py           # ML pipeline logic
│   ├── schemas.py           # Data models
│   ├── job_manager.py       # Async job tracking
│   ├── utils.py             # Helper functions
│   ├── config.py            # Configuration
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example         # Environment template
│   ├── Dockerfile           # Container definition
│   ├── docker-compose.yml   # Compose orchestration
│   └── README.md            # Backend docs
│
└── frontend/                 # React application
    ├── src/
    │   ├── components/      # React components
    │   ├── services/        # API client
    │   ├── styles/          # Styling
    │   ├── App.jsx          # Main component
    │   └── main.jsx         # Entry point
    ├── package.json         # Node dependencies
    ├── vite.config.js       # Build config
    ├── index.html           # HTML template
    ├── .env.example         # Environment template
    └── README.md            # Frontend docs
```

## 🔑 Key Components

### Backend API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Welcome message |
| `/health` | GET | Health check |
| `/info` | GET | API information |
| `/upload` | POST | Upload dataset |
| `/pipeline/profile` | POST | Profile dataset |
| `/pipeline/audit` | POST | AI quality audit |
| `/pipeline/preprocess` | POST | Preprocess data |
| `/pipeline/train` | POST | Train models |
| `/pipeline/run` | POST | Full pipeline (async) |
| `/jobs` | GET | List all jobs |
| `/jobs/{job_id}` | GET | Get job status |
| `/predict` | POST | Make predictions |

### Frontend Features

- **Upload Interface**: File selection with validation
- **Pipeline Visualization**: 6-step progress tracking
- **Real-time Status**: Live job monitoring
- **Results Display**: Metrics, charts, and insights
- **Error Handling**: User-friendly error messages

### AI Pipeline Stages

1. **Profile** (Statistical Analysis)
   - Row/column count
   - Data types
   - Missing values
   - Target distribution

2. **Audit** (AI Quality Check)
   - Uses Groq LLM
   - Detects data quality issues
   - Provides recommendations
   - Severity levels: high, medium, low

3. **Preprocess** (Data Cleaning)
   - Missing value imputation
   - Outlier detection
   - Duplicate removal (updated logic)
   - VIF-based multicollinearity removal
   - RobustScaler for skewed data
   - PowerTransformer normalization

4. **Feature Engineering**
   - Automatic feature scaling
   - Feature interaction detection
   - Dimensionality reduction

5. **Training** (Model Selection)
   - Multiple model types
   - Automatic hyperparameter tuning
   - Overfitting detection
   - Cross-validation

6. **Evaluation** (Results Analysis)
   - Accuracy metrics
   - F1 scores
   - Generalization status
   - Model comparison

## 🔧 Configuration

### Backend (.env)

```env
# Groq API Configuration
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Server Configuration
HOST=0.0.0.0
PORT=8000

# File Limits
MAX_UPLOAD_SIZE_MB=100

# Job Configuration
JOB_TIMEOUT_SECONDS=3600
MAX_CONCURRENT_JOBS=5

# Database
DATABASE_URL=sqlite:///./automl.db

# Logging
LOG_LEVEL=INFO
```

### Frontend (.env)

```env
REACT_APP_API_URL=http://localhost:8000
VITE_API_URL=http://localhost:8000
```

## 🧪 Testing the Integration

### Manual Test Flow

1. **Start Backend**
   ```bash
   cd automl-backend
   uvicorn main:app --reload
   ```

2. **Start Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test Upload**
   - Navigate to http://localhost:3000
   - Upload a test CSV file
   - Select target column
   - Click upload

4. **Monitor Pipeline**
   - Watch each stage complete
   - Check job ID in console
   - Review progress percentage

5. **Verify Results**
   - See model metrics
   - Check generalization status
   - Review data quality flags

### Using Test API Script

```bash
cd automl-backend
python test_api.py
```

## 🐳 Docker Deployment

### Build & Run with Docker Compose

```bash
cd automl-backend

# Build images
docker-compose build

# Start services
docker-compose up

# Access:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:3000
```

## 🚨 Troubleshooting

### Frontend Won't Connect to Backend

**Problem**: "Cannot connect to backend" error

**Solutions**:
1. Ensure backend is running on http://localhost:8000
2. Check if port 8000 is not blocked by firewall
3. Verify CORS is enabled in main.py
4. Check console for specific error messages

### Upload Fails

**Problem**: File upload fails with 413 or 422 error

**Solutions**:
1. Ensure file size < 100MB
2. Check file format is CSV/Excel/JSON
3. Verify target column name is correct
4. Check server logs for details

### Pipeline Hangs

**Problem**: Pipeline stops responding

**Solutions**:
1. Check backend logs for errors
2. Verify Groq API key is valid
3. Check job timeout setting (default 3600s)
4. Restart backend server

### Dataset Preview Not Showing

**Problem**: No data preview displayed

**Solutions**:
1. Try smaller file first
2. Verify CSV structure is valid
3. Check if file has headers
4. Review backend error logs

## 📊 Performance Tips

### Backend Optimization
- Use connection pooling for databases
- Cache model artifacts
- Implement request rate limiting
- Monitor system resources

### Frontend Optimization
- Use production build for deployment
- Enable gzip compression
- Minimize bundle size
- Lazy load components

## 🔒 Security Considerations

1. **API Keys**
   - Never commit .env files
   - Use environment variables
   - Rotate keys regularly

2. **File Uploads**
   - Validate file types
   - Check file sizes
   - Scan for malicious content
   - Use temporary storage

3. **Data Privacy**
   - Don't store raw data permanently
   - Encrypt sensitive information
   - Implement access controls
   - Add audit logging

## 🎯 Next Steps

### Short Term
- [ ] Test with real datasets
- [ ] Customize pipeline stages
- [ ] Add more ML models
- [ ] Improve UI/UX

### Medium Term
- [ ] Add user authentication
- [ ] Implement data persistence (PostgreSQL)
- [ ] Add prediction interface
- [ ] Create admin dashboard

### Long Term
- [ ] Mobile app version
- [ ] Advanced visualizations
- [ ] Model marketplace
- [ ] Collaborative features

## 📚 Documentation

- [Backend README](automl-backend/README.md)
- [Frontend README](frontend/README.md)
- [Backend Integration Summary](automl-backend/INTEGRATION_SUMMARY.md)
- [Backend Quick Start Guide](automl-backend/QUICKSTART_GUIDE.md)
- [API Examples](automl-backend/API_EXAMPLES.sh)

## 💡 Tips & Tricks

### Quick Development Workflow

```bash
# Terminal 1: Backend
cd automl-backend
uvicorn main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Testing
cd automl-backend
python test_api.py
```

### Testing with curl

```bash
# Upload file
curl -F "file=@data.csv" \
  -F "target_column=target" \
  http://localhost:8000/upload

# Check health
curl http://localhost:8000/health

# Get API info
curl http://localhost:8000/info
```


### Common Issues

**Problem**: Slow pipeline
- **Cause**: Large dataset, slow hardware
- **Solution**: Start with smaller files, upgrade resources

**Problem**: Memory errors
- **Cause**: Very large dataset
- **Solution**: Increase available memory, use data sampling

**Problem**: CORS errors
- **Cause**: Frontend and backend on different origins
- **Solution**: Configure CORS correctly in backend


