"""Utility functions for pipeline integration."""
import os
import json
import shutil
from pathlib import Path
from typing import Tuple, Dict, Any, List
import pandas as pd
import logging

from config import UPLOAD_DIR, MODELS_DIR, RESULTS_DIR
from job_manager import job_manager

logger = logging.getLogger(__name__)


def save_uploaded_file(file_path: str, dataset_id: str) -> str:
    """Save uploaded file to dataset directory."""
    dataset_dir = UPLOAD_DIR / dataset_id
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    dest_path = dataset_dir / Path(file_path).name
    shutil.copy(file_path, dest_path)
    
    logger.info(f"Saved file to {dest_path}")
    return str(dest_path)


def save_results(job_id: str, results: Dict[str, Any]) -> str:
    """Save pipeline results to file."""
    results_dir = RESULTS_DIR / job_id
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Save full results as JSON
    results_file = results_dir / "results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Saved results to {results_file}")
    return str(results_file)


def save_model(job_id: str, model_name: str, model_obj) -> str:
    """Save trained model using pickle."""
    import pickle
    
    model_dir = MODELS_DIR / job_id
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model_file = model_dir / f"{model_name}.pkl"
    with open(model_file, 'wb') as f:
        pickle.dump(model_obj, f)
    
    logger.info(f"Saved model to {model_file}")
    return str(model_file)


def load_model(job_id: str, model_name: str):
    """Load trained model."""
    import pickle
    
    model_file = MODELS_DIR / job_id / f"{model_name}.pkl"
    if not model_file.exists():
        raise FileNotFoundError(f"Model not found: {model_file}")
    
    with open(model_file, 'rb') as f:
        model = pickle.load(f)
    
    logger.info(f"Loaded model from {model_file}")
    return model


def convert_profile_to_schema(profile: Dict[str, Any]):
    """Convert raw profile dict to ProfileResponse schema."""
    from schemas import DatasetProfile, ColumnProfile, TaskType
    
    # Build column profiles
    columns = {}
    for col_name, col_stats in profile.get("columns", {}).items():
        columns[col_name] = ColumnProfile(**col_stats)
    
    # Map task type
    task_type_map = {
        "binary": TaskType.BINARY_CLASSIFICATION,
        "multiclass": TaskType.MULTICLASS_CLASSIFICATION,
        "regression": TaskType.REGRESSION,
    }
    target_type_raw = profile["global"]["target_type"]
    # Handle both "binary" and "binary classification" formats
    for key, value in task_type_map.items():
        if key in target_type_raw:
            task_type = value
            break
    else:
        task_type = TaskType.BINARY_CLASSIFICATION
    
    return DatasetProfile(
        shape=profile["shape"],
        total_null_cells=profile["global"]["total_null_cells"],
        total_null_pct=profile["global"]["total_null_pct"],
        target_col=profile["global"]["target_col"],
        target_type=task_type,
        target_balance=profile["global"]["target_balance"],
        columns=columns,
        severe_class_imbalance=profile["global"].get("severe_class_imbalance", False),
    )


def convert_flags_to_schema(flags: List[Dict[str, Any]]):
    """Convert raw flag dicts to DataQualityFlag schema."""
    from schemas import DataQualityFlag, IssueType, SeverityLevel
    
    result = []
    for flag in flags:
        result.append(DataQualityFlag(
            id=flag.get("id"),
            column=flag.get("column"),
            issue_type=IssueType(flag.get("issue_type")),
            severity=SeverityLevel(flag.get("severity")),
            detail=flag.get("detail"),
            recommended_fix=flag.get("recommended_fix"),
            auto_fixable=flag.get("auto_fixable", False),
        ))
    return result


def convert_metrics_to_schema(results: Dict[str, Dict[str, Any]]):
    """Convert raw eval results to ModelMetrics schema."""
    from schemas import ModelMetrics
    
    metrics_dict = {}
    for model_name, metrics in results.items():
        # Determine generalization status
        train_test_gap = metrics.get("train_test_gap", 0)
        if train_test_gap > 0.15:
            status = "OVERFITTING"
        elif metrics.get("train_accuracy", 0) < 0.60 and metrics.get("accuracy", 0) < 0.65:
            status = "UNDERFITTING"
        elif (abs(train_test_gap) < 0.05 and 
              abs(metrics.get("test_cv_gap", 0)) < 0.05 and 
              metrics.get("accuracy", 0) >= 0.85):
            status = "EXCELLENT"
        elif train_test_gap < 0.10:
            status = "GOOD"
        else:
            status = "BALANCED"
        
        metrics_dict[model_name] = ModelMetrics(
            model_name=model_name,
            train_accuracy=metrics.get("train_accuracy", 0),
            accuracy=metrics.get("accuracy", 0),
            f1_weighted=metrics.get("f1_weighted", 0),
            precision=metrics.get("precision", 0),
            recall=metrics.get("recall", 0),
            roc_auc=metrics.get("roc_auc"),
            cv_mean=metrics.get("cv_mean", 0),
            cv_std=metrics.get("cv_std", 0),
            train_time=metrics.get("train_time", 0),
            train_test_gap=metrics.get("train_test_gap", 0),
            test_cv_gap=metrics.get("test_cv_gap", 0),
            generalization_status=status,
        )
    
    return metrics_dict


def filter_flags_by_approval(flags: List[Dict[str, Any]], approved_ids: List[str] = None, skip_issues: List[str] = None) -> List[Dict[str, Any]]:
    """Filter flags based on approval IDs and skip issues."""
    filtered = flags
    
    # Filter by approved IDs
    if approved_ids:
        filtered = [f for f in filtered if f["id"] in approved_ids]
    
    # Filter out skip issues
    if skip_issues:
        filtered = [f for f in filtered if f["issue_type"] not in skip_issues]
    
    return filtered


def get_available_models() -> List[str]:
    """Get list of available models."""
    models = [
        "logistic_regression",
        "random_forest",
        "gradient_boosting",
        "knn",
        "svm",
        "mlp",
    ]
    
    try:
        import xgboost  # noqa
        models.append("xgboost")
    except ImportError:
        pass
    
    try:
        import lightgbm  # noqa
        models.append("lightgbm")
    except ImportError:
        pass
    
    return models


def validate_file_size(file_path: str, max_size_mb: int = 100) -> bool:
    """Validate file size."""
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    return file_size_mb <= max_size_mb


def cleanup_dataset(dataset_id: str):
    """Clean up dataset files."""
    dataset_dir = UPLOAD_DIR / dataset_id
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir)
        logger.info(f"Cleaned up dataset {dataset_id}")


def get_dataset_preview(file_path: str, nrows: int = 5) -> pd.DataFrame:
    """Get preview of dataset."""
    ext = Path(file_path).suffix.lower()
    
    if ext == ".csv":
        return pd.read_csv(file_path, nrows=nrows)
    elif ext in (".xlsx", ".xls"):
        return pd.read_excel(file_path, nrows=nrows)
    elif ext == ".json":
        return pd.read_json(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
