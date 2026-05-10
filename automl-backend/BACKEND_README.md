# AutoML Pipeline Backend

End-to-end AutoML system with AI-powered data quality auditing using FastAPI and Groq.

## Features

- 📤 **File Upload**: Support for CSV, Excel, JSON datasets
- 🔍 **AI Data Audit**: Automatic data quality assessment using Groq LLM
- 🔧 **Automated Preprocessing**: Smart handling of missing values, outliers, skewness
- ⚡ **Multiple Models**: Train Random Forest, XGBoost, LightGBM, Logistic Regression, KNN, SVM, MLP
- 📊 **Comprehensive Evaluation**: Train/Test/CV metrics with generalization analysis
- 🎯 **Automatic Overfitting Detection**: Identifies and corrects overfitting/underfitting
- 💾 **Model Persistence**: Save and load trained models
- 🔄 **Async Job Management**: Track long-running pipeline jobs
- 🌐 **RESTful API**: Complete API with Swagger documentation

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```
GROQ_API_KEY=gsk_your_key_here
```

Get your free Groq API key from: https://console.groq.com

### 3. Run the Server

```bash
uvicorn main:app --reload
```

Server runs at: `http://localhost:8000`

API documentation (Swagger): `http://localhost:8000/docs`

## API Endpoints

### Health & Info

```
GET  /                    # API info
GET  /health              # Health check
GET  /info                # Available models and formats
```

### File Upload

```
POST /upload              # Upload dataset file
```

Request:
```bash
curl -F "file=@data.csv" -F "target_column=target" http://localhost:8000/upload
```

### Pipeline Operations

```
POST /pipeline/profile    # Profile dataset (stats only)
POST /pipeline/audit      # Run AI audit
POST /pipeline/preprocess # Preprocess with audit flags
POST /pipeline/train      # Train models
POST /pipeline/run        # Full end-to-end pipeline
```

### Job Management

```
GET  /jobs                # List all jobs
GET  /jobs/{job_id}       # Get specific job status
```

### Predictions

```
POST /predict             # Make predictions with trained model
```

## Usage Examples

### 1. Upload and Profile Dataset

```bash
# Upload file and get preview
curl -F "file=@heart.csv" \
  http://localhost:8000/upload
```

### 2. Run Full Pipeline (Background)

```bash
curl -X POST http://localhost:8000/pipeline/run \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "uploads/heart.csv",
    "target_column": "target",
    "apply_audit_fixes": true,
    "training_config": {
      "models": ["xgboost", "random_forest"],
      "cv_folds": 5,
      "n_iter": 15
    }
  }'
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started"
}
```

### 3. Check Job Progress

```bash
curl http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 65,
  "current_stage": "Training models",
  "created_at": "2026-05-10T12:00:00",
  "updated_at": "2026-05-10T12:05:30"
}
```

### 4. Get Training Results

```bash
curl http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000 | jq .result
```

### 5. Make Predictions

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "data": [
      {
        "age": 45,
        "sex": 1,
        "cp": 3,
        "trestbps": 140,
        ...
      }
    ]
  }'
```

## Project Structure

```
automl-backend/
├── main.py                 # FastAPI app with all endpoints
├── config.py               # Configuration management
├── schemas.py              # Pydantic request/response models
├── job_manager.py          # Async job management
├── utils.py                # Helper functions
├── auto_ai.py              # AutoML pipeline logic
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── .env                    # Your actual environment (git-ignored)
├── uploads/                # Uploaded datasets
├── models/                 # Trained models (by job_id)
├── results/                # Pipeline results (by job_id)
└── logs/                   # Application logs
```

## Key Features

### 1. Automated Data Quality Audit

Uses Groq's LLM to analyze dataset statistics (not raw data for privacy):
- Detects missing values, outliers, skewness
- Identifies class imbalance and multicollinearity
- Suggests fixes with severity levels (high/medium/low)

### 2. Intelligent Preprocessing

Applied based on audit recommendations:
- **Imputation**: IterativeImputer, KNNImputer, mean/median
- **Outlier Detection**: IsolationForest, IQR, Z-score clipping
- **Transformation**: Yeo-Johnson, log1p for skewed distributions
- **Scaling**: StandardScaler for normal data, RobustScaler for outliers
- **Encoding**: One-hot for low-cardinality, label-encoding for high-cardinality
- **Multicollinearity**: VIF-based feature removal

### 3. Overfitting Detection & Prevention

**Detection Metrics:**
- Train vs Test accuracy gap (primary indicator)
- Train vs CV mean gap
- Test vs CV mean gap

**Automatic Correction:**
- Reduces learning rate and regularization strength
- Increases regularization (L1/L2) for tree models
- Adds early stopping and validation splits for neural networks
- Simplifies model architectures

### 4. Available Models

- **Logistic Regression** - Fast, interpretable baseline
- **Random Forest** - Ensemble tree model
- **Gradient Boosting** - Powerful sequential boosting
- **XGBoost** - Optimized gradient boosting
- **LightGBM** - Fast gradient boosting
- **K-Nearest Neighbors** - Non-parametric method
- **Support Vector Machine** - Kernel-based classifier
- **Neural Networks (MLP)** - Deep learning baseline

### 5. Comprehensive Evaluation

For each model:
- Train accuracy, Test accuracy, CV mean + std
- F1, Precision, Recall (weighted for multiclass)
- ROC-AUC (binary/multiclass OvR)
- Confusion matrix
- Feature importance/coefficients
- Generalization status (Excellent/Good/Balanced/Overfitting/Underfitting)

### 6. Job Management

Async job processing with:
- Job status tracking (pending → running → completed/failed)
- Progress indicators (0-100%)
- Current stage description
- Error handling and logging
- Automatic cleanup of old jobs

## Configuration

### Environment Variables (.env)

```
# Required
GROQ_API_KEY=gsk_...

# Optional
GROQ_MODEL=llama-3.3-70b-versatile
DATABASE_URL=sqlite:///./automl.db
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

### Customizing Pipeline

Create a `TrainingConfig` object:

```python
{
  "models": ["xgboost", "random_forest", "logistic_regression"],
  "cv_folds": 10,
  "n_iter": 30,
  "random_seed": 42,
  "test_size": 0.2
}
```

## Performance Tips

1. **Reduce n_iter** for faster hyperparameter tuning (default: 15)
2. **Reduce cv_folds** for fewer cross-validations (default: 5)
3. **Select fewer models** to train (default: logistic_regression, random_forest, xgboost)
4. **Use LightGBM** instead of XGBoost for large datasets (faster)
5. **Increase MAX_CONCURRENT_JOBS** for parallel pipelines (caution: memory usage)

## Troubleshooting

### GROQ_API_KEY not set

```
Error: GROQ_API_KEY not set
```

**Solution**: Add your Groq API key to `.env`:
```
GROQ_API_KEY=gsk_your_key_here
```

### File too large

```
Error: File too large (max 100 MB)
```

**Solution**: Increase MAX_UPLOAD_SIZE in config.py or split your dataset

### Out of memory during training

```
Solution: 
1. Reduce n_iter or cv_folds
2. Train fewer models
3. Reduce dataset size
4. Use LightGBM instead of other models
```

## API Response Examples

### Job Status (Running)

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_type": "full_pipeline",
  "status": "running",
  "progress": 45,
  "current_stage": "Training models",
  "created_at": "2026-05-10T12:00:00.000000",
  "updated_at": "2026-05-10T12:05:00.000000",
  "completed_at": null,
  "error": null
}
```

### Model Metrics

```json
{
  "model_name": "xgboost",
  "train_accuracy": 0.9950,
  "accuracy": 0.9951,
  "f1_weighted": 0.9951,
  "precision": 0.9952,
  "recall": 0.9951,
  "roc_auc": 0.9950,
  "cv_mean": 0.9866,
  "cv_std": 0.0105,
  "train_time": 4.63,
  "train_test_gap": 0.0001,
  "test_cv_gap": 0.0085,
  "generalization_status": "EXCELLENT"
}
```

## Future Enhancements

- [ ] Model versioning and comparison
- [ ] Feature extraction and engineering suggestions
- [ ] Hyperparameter optimization (Optuna, Ray Tune)
- [ ] Model explainability (SHAP, LIME)
- [ ] Real-time model monitoring and drift detection
- [ ] Automated retraining pipelines
- [ ] Multi-GPU training support
- [ ] Production deployment guides (Docker, Kubernetes)

## License

MIT

## Support

For issues, questions, or contributions, please open an issue or submit a pull request.
