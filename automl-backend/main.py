"""FastAPI backend for AutoML Pipeline."""
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import (
    API_TITLE, API_VERSION, API_DESCRIPTION,
    ALLOWED_ORIGINS, UPLOAD_DIR, MAX_UPLOAD_SIZE
)
from schemas import (
    DatasetUploadRequest, AuditResponse, PreprocessingResponse,
    TrainingResponse, PipelineRequest, PipelineResponse, JobStatus,
    APIInfo, HealthCheck, PredictionRequest, PredictionResponse
)
from job_manager import job_manager
from utils import (
    validate_file_size, get_available_models, save_uploaded_file,
    save_results, save_model, load_model, convert_profile_to_schema,
    convert_flags_to_schema, convert_metrics_to_schema, filter_flags_by_approval,
    get_dataset_preview
)

# ─── Logging Configuration ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ─── FastAPI Setup ──────────────────────────────────────────────────────
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
)

# ─── CORS Configuration ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Create upload directory ────────────────────────────────────────────
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════
# HEALTH CHECK & INFO ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "message": "AutoML Pipeline API",
        "version": API_VERSION,
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """Check API health status."""
    import os
    groq_status = "✓" if os.getenv("GROQ_API_KEY") else "✗"
    
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=API_VERSION,
        database="sqlite",
        groq_api=groq_status,
    )


@app.get("/info", response_model=APIInfo, tags=["Info"])
async def api_info():
    """Get API information."""
    return APIInfo(
        name=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        available_models=get_available_models(),
        supported_formats=[".csv", ".xlsx", ".xls", ".json"],
        max_file_size_mb=MAX_UPLOAD_SIZE // (1024 * 1024),
    )


# ═══════════════════════════════════════════════════════════════════════════
# FILE UPLOAD ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/upload", tags=["Upload"])
async def upload_dataset(
    file: UploadFile = File(...),
    target_column: str = None,
):
    """Upload dataset file."""
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in {".csv", ".xlsx", ".xls", ".json"}:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file_ext}"
            )
        
        # Save uploaded file
        contents = await file.read()
        temp_path = UPLOAD_DIR / file.filename
        with open(temp_path, 'wb') as f:
            f.write(contents)
        
        # Validate file size
        if not validate_file_size(str(temp_path)):
            temp_path.unlink()
            raise HTTPException(
                status_code=413,
                detail=f"File too large (max {MAX_UPLOAD_SIZE // (1024*1024)} MB)"
            )
        
        # Get dataset preview
        preview_df = get_dataset_preview(str(temp_path), nrows=5)
        
        return {
            "filename": file.filename,
            "size_bytes": len(contents),
            "columns": list(preview_df.columns),
            "rows": len(preview_df),
            "preview": preview_df.head().to_dict(orient="records"),
            "temp_path": str(temp_path),
        }
    
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# JOB MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/jobs/{job_id}", tags=["Jobs"])
async def get_job_status(job_id: str):
    """Get job status."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return job.to_dict()


@app.get("/jobs", tags=["Jobs"])
async def list_jobs():
    """List all jobs."""
    return {
        "total_jobs": len(job_manager.jobs),
        "jobs": [job.to_dict() for job in job_manager.jobs.values()]
    }


# ═══════════════════════════════════════════════════════════════════════════
# PIPELINE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/pipeline/profile", tags=["Pipeline"])
async def profile_dataset(
    file_path: str,
    target_column: str,
):
    """Profile dataset without running full pipeline."""
    from auto_ai import build_profile, _read_file
    
    job_id = job_manager.create_job("profile")
    
    try:
        job_manager.update_job(job_id, 10, "Loading dataset")
        df = _read_file(file_path)
        
        job_manager.update_job(job_id, 30, "Building profile")
        profile = build_profile(df, target_column)
        
        job_manager.update_job(job_id, 100, "Profile complete")
        
        # Convert to schema
        profile_schema = convert_profile_to_schema(profile)
        
        result = {
            "profile": profile_schema.dict(),
            "job_id": job_id,
        }
        
        job_manager.complete_job(job_id, result)
        return result
    
    except Exception as e:
        logger.error(f"Profiling error: {str(e)}")
        job_manager.fail_job(job_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline/audit", tags=["Pipeline"])
async def run_audit(
    file_path: str,
    target_column: str,
    groq_model: str = None,
):
    """Run AI audit on dataset."""
    from auto_ai import build_profile, run_ai_audit, _read_file
    
    job_id = job_manager.create_job("audit")
    
    try:
        job_manager.update_job(job_id, 10, "Loading dataset")
        df = _read_file(file_path)
        
        job_manager.update_job(job_id, 30, "Building profile")
        profile = build_profile(df, target_column)
        
        job_manager.update_job(job_id, 50, "Running AI audit")
        flags = run_ai_audit(profile, groq_model=groq_model)
        
        job_manager.update_job(job_id, 100, "Audit complete")
        
        # Convert to schema
        flags_schema = convert_flags_to_schema(flags)
        
        high = len([f for f in flags_schema if f.severity.value == "high"])
        medium = len([f for f in flags_schema if f.severity.value == "medium"])
        low = len([f for f in flags_schema if f.severity.value == "low"])
        
        response = AuditResponse(
            job_id=job_id,
            flags=flags_schema,
            total_issues=len(flags_schema),
            high_severity=high,
            medium_severity=medium,
            low_severity=low,
        )
        
        job_manager.complete_job(job_id, response.dict())
        return response
    
    except Exception as e:
        logger.error(f"Audit error: {str(e)}")
        job_manager.fail_job(job_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline/preprocess", tags=["Pipeline"])
async def preprocess_dataset(
    file_path: str,
    target_column: str,
    approved_flags: list = None,
    skip_issues: list = None,
):
    """Preprocess dataset based on audit flags."""
    from auto_ai import build_profile, run_ai_audit, apply_preprocessing, _read_file
    
    job_id = job_manager.create_job("preprocess")
    
    try:
        job_manager.update_job(job_id, 10, "Loading dataset")
        df = _read_file(file_path)
        original_shape = df.shape
        
        job_manager.update_job(job_id, 20, "Building profile")
        profile = build_profile(df, target_column)
        
        job_manager.update_job(job_id, 40, "Running audit")
        flags = run_ai_audit(profile)
        
        # Filter flags
        filtered_flags = filter_flags_by_approval(flags, approved_flags, skip_issues)
        
        job_manager.update_job(job_id, 60, "Applying preprocessing")
        df_clean, log = apply_preprocessing(df.copy(), filtered_flags, target_column)
        
        job_manager.update_job(job_id, 100, "Preprocessing complete")
        
        # Save cleaned dataset
        cleaned_path = UPLOAD_DIR / f"cleaned_{Path(file_path).name}"
        if file_path.endswith('.csv'):
            df_clean.to_csv(cleaned_path, index=False)
        else:
            df_clean.to_parquet(cleaned_path)
        
        response = PreprocessingResponse(
            job_id=job_id,
            original_shape=original_shape,
            cleaned_shape=df_clean.shape,
            log=[{"step": i, "action": str(l), "status": "success"} for i, l in enumerate(log)],
            success=True,
        )
        
        job_manager.complete_job(job_id, response.dict())
        return response
    
    except Exception as e:
        logger.error(f"Preprocessing error: {str(e)}")
        job_manager.fail_job(job_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline/train", tags=["Pipeline"])
async def train_models(
    file_path: str,
    target_column: str,
    models: list = None,
    cv_folds: int = 5,
    n_iter: int = 15,
):
    """Train models on preprocessed dataset."""
    from auto_ai import (
        _read_file, build_profile, run_ai_audit, apply_preprocessing,
        run_feature_engineering, train_models, evaluate_all
    )
    
    if models is None:
        models = ["logistic_regression", "random_forest", "xgboost"]
    
    job_id = job_manager.create_job("train")
    
    try:
        job_manager.update_job(job_id, 5, "Loading dataset")
        df = _read_file(file_path)
        
        job_manager.update_job(job_id, 10, "Profiling and auditing")
        profile = build_profile(df, target_column)
        flags = run_ai_audit(profile)
        
        job_manager.update_job(job_id, 20, "Preprocessing")
        df_clean, _ = apply_preprocessing(df.copy(), flags, target_column)
        
        job_manager.update_job(job_id, 30, "Feature engineering")
        X_train, X_test, y_train, y_test, features, task_type = run_feature_engineering(
            df_clean, target_column, flags
        )
        
        job_manager.update_job(job_id, 50, f"Training {len(models)} models")
        trained = train_models(models, X_train, y_train, n_iter=n_iter, cv=cv_folds)
        
        job_manager.update_job(job_id, 80, "Evaluating models")
        eval_results = evaluate_all(trained, X_test, y_test, X_train, y_train)
        
        # Save models
        for model_name, model_obj in trained.items():
            save_model(job_id, model_name, model_obj["model"])
        
        job_manager.update_job(job_id, 100, "Training complete")
        
        # Convert metrics to schema
        metrics = convert_metrics_to_schema(eval_results)
        
        # Find best model
        best_model = max(metrics.items(), key=lambda x: x[1].f1_weighted)
        
        response = TrainingResponse(
            job_id=job_id,
            task_type=task_type.upper().replace("_", " "),
            models_trained=list(trained.keys()),
            best_model=best_model[0],
            best_score=best_model[1].f1_weighted,
            training_time=sum(m.train_time for m in metrics.values()),
            metrics={k: v.dict() for k, v in metrics.items()},
        )
        
        job_manager.complete_job(job_id, response.dict())
        return response
    
    except Exception as e:
        logger.error(f"Training error: {str(e)}")
        job_manager.fail_job(job_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline/run", tags=["Pipeline"])
async def run_full_pipeline(
    file_path: str,
    request: PipelineRequest,
    background_tasks: BackgroundTasks,
):
    """Run full AutoML pipeline end-to-end."""
    from auto_ai import (
        _read_file, build_profile, run_ai_audit, apply_preprocessing,
        run_feature_engineering, train_models, evaluate_all
    )
    
    job_id = job_manager.create_job("full_pipeline")
    
    async def pipeline_worker():
        try:
            job_manager.start_job(job_id)
            job_manager.update_job(job_id, 5, "Loading dataset")
            df = _read_file(file_path)
            
            job_manager.update_job(job_id, 10, "Profiling dataset")
            profile = build_profile(df, request.target_column)
            profile_schema = convert_profile_to_schema(profile)
            
            job_manager.update_job(job_id, 20, "Running AI audit")
            flags = run_ai_audit(profile, groq_model=request.groq_model)
            flags_schema = convert_flags_to_schema(flags)
            
            if request.apply_audit_fixes:
                filtered_flags = filter_flags_by_approval(flags, skip_issues=request.skip_issues)
            else:
                filtered_flags = []
            
            job_manager.update_job(job_id, 35, "Preprocessing")
            df_clean, preproc_log = apply_preprocessing(df.copy(), filtered_flags, request.target_column)
            preproc_log_schema = [{"step": i, "action": str(l), "status": "success"} 
                                 for i, l in enumerate(preproc_log)]
            
            job_manager.update_job(job_id, 50, "Feature engineering")
            X_train, X_test, y_train, y_test, features, task_type = run_feature_engineering(
                df_clean, request.target_column, filtered_flags
            )
            
            training_config = request.training_config or __import__("schemas").TrainingConfig()
            job_manager.update_job(job_id, 60, f"Training {len(training_config.models)} models")
            trained = train_models(
                training_config.models, X_train, y_train,
                n_iter=training_config.n_iter, cv=training_config.cv_folds
            )
            
            job_manager.update_job(job_id, 85, "Evaluating models")
            eval_results = evaluate_all(trained, X_test, y_test, X_train, y_train)
            
            # Save models
            for model_name, model_obj in trained.items():
                save_model(job_id, model_name, model_obj["model"])
            
            metrics = convert_metrics_to_schema(eval_results)
            best_model = max(metrics.items(), key=lambda x: x[1].f1_weighted)
            
            training_response = TrainingResponse(
                job_id=job_id,
                task_type=task_type,
                models_trained=list(trained.keys()),
                best_model=best_model[0],
                best_score=best_model[1].f1_weighted,
                training_time=sum(m.train_time for m in metrics.values()),
                metrics={k: v.dict() for k, v in metrics.items()},
            )
            
            job_manager.update_job(job_id, 100, "Pipeline complete")
            
            # Final result
            result = {
                "dataset_profile": profile_schema.dict(),
                "audit_flags": [f.dict() for f in flags_schema],
                "preprocessing_log": preproc_log_schema,
                "training_results": training_response.dict(),
            }
            
            job_manager.complete_job(job_id, result)
        
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            job_manager.fail_job(job_id, str(e))
    
    # Run in background
    background_tasks.add_task(pipeline_worker)
    
    return {"job_id": job_id, "status": "started"}


# ═══════════════════════════════════════════════════════════════════════════
# PREDICTION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(request: PredictionRequest):
    """Make predictions using trained model."""
    try:
        import pandas as pd
        
        # Load best model from job
        job = job_manager.get_job(request.job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {request.job_id} not found")
        
        if job.status != "completed":
            raise HTTPException(status_code=400, detail=f"Job {request.job_id} is not completed")
        
        # Get best model name from results
        best_model_name = job.result.get("training_results", {}).get("best_model")
        if not best_model_name:
            raise HTTPException(status_code=400, detail="No trained model found in job")
        
        # Load model
        model = load_model(request.job_id, best_model_name)
        
        # Prepare data
        df = pd.DataFrame(request.data)
        
        # Make predictions
        predictions = model.predict(df)
        
        # Get probabilities if available
        probabilities = None
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(df).tolist()
        
        return PredictionResponse(
            predictions=[{"prediction": str(p)} for p in predictions],
            probabilities=probabilities,
            model_used=best_model_name,
        )
    
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
