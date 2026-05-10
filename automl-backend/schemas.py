"""Pydantic schemas for API requests/responses."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class TaskType(str, Enum):
    """Task type enumeration."""
    BINARY_CLASSIFICATION = "binary_classification"
    MULTICLASS_CLASSIFICATION = "multiclass_classification"
    REGRESSION = "regression"


class SeverityLevel(str, Enum):
    """Severity level enumeration."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueType(str, Enum):
    """Data quality issue types."""
    MISSING_VALUES = "missing_values"
    OUTLIERS = "outliers"
    HIGH_SKEW = "high_skew"
    CLASS_IMBALANCE = "class_imbalance"
    WRONG_DTYPE = "wrong_dtype"
    HIGH_CARDINALITY = "high_cardinality"
    CONSTANT_COLUMN = "constant_column"
    NEAR_ZERO_VARIANCE = "near_zero_variance"
    HIGH_MULTICOLLINEARITY = "high_multicollinearity"
    DISTRIBUTION_ANOMALY = "distribution_anomaly"


# ─── Upload & Dataset ────────────────────────────────────────────────────
class DatasetUploadRequest(BaseModel):
    """Request to upload and process dataset."""
    target_column: str = Field(..., description="Name of target column")
    groq_model: Optional[str] = Field(None, description="Groq model to use for audit")


class ColumnProfile(BaseModel):
    """Statistical profile of a column."""
    dtype: str
    null_count: int
    null_pct: float
    kind: str  # numeric or categorical
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    unique_count: Optional[int] = None
    outlier_count: Optional[int] = None
    outlier_pct: Optional[float] = None


class DatasetProfile(BaseModel):
    """Statistical profile of entire dataset."""
    shape: Dict[str, int]  # rows, cols
    total_null_cells: int
    total_null_pct: float
    target_col: str
    target_type: TaskType
    target_balance: Dict[str, float]
    columns: Dict[str, ColumnProfile]
    severe_class_imbalance: Optional[bool] = False


# ─── AI Audit ────────────────────────────────────────────────────────────
class DataQualityFlag(BaseModel):
    """Single data quality issue flag."""
    id: str
    column: str
    issue_type: IssueType
    severity: SeverityLevel
    detail: str
    recommended_fix: str
    auto_fixable: bool


class AuditRequest(BaseModel):
    """Request for AI audit."""
    apply_all: bool = Field(default=True, description="Apply all recommended fixes")
    approved_flags: Optional[List[str]] = Field(None, description="Specific flag IDs to approve")
    skip_issues: Optional[List[IssueType]] = Field(None, description="Issues to skip")


class AuditResponse(BaseModel):
    """AI audit response."""
    job_id: str
    flags: List[DataQualityFlag]
    total_issues: int
    high_severity: int
    medium_severity: int
    low_severity: int


# ─── Preprocessing ──────────────────────────────────────────────────────
class PreprocessingLogEntry(BaseModel):
    """Single preprocessing step log."""
    step: str
    action: str
    status: str  # success, warning, error


class PreprocessingResponse(BaseModel):
    """Preprocessing results."""
    job_id: str
    original_shape: tuple
    cleaned_shape: tuple
    log: List[PreprocessingLogEntry]
    success: bool


# ─── Training Configuration ─────────────────────────────────────────────
class TrainingConfig(BaseModel):
    """Model training configuration."""
    models: List[str] = Field(
        default=["logistic_regression", "random_forest", "xgboost"],
        description="Models to train"
    )
    cv_folds: int = Field(default=5, ge=2, le=20, description="Number of CV folds")
    n_iter: int = Field(default=15, ge=5, le=100, description="Hyperparameter search iterations")
    random_seed: int = Field(default=42, description="Random seed for reproducibility")
    test_size: float = Field(default=0.2, ge=0.1, le=0.5, description="Test set fraction")


class ModelMetrics(BaseModel):
    """Individual model evaluation metrics."""
    model_name: str
    train_accuracy: float
    accuracy: float
    f1_weighted: float
    precision: float
    recall: float
    roc_auc: Optional[float] = None
    cv_mean: float
    cv_std: float
    train_time: float
    train_test_gap: float
    test_cv_gap: float
    generalization_status: str  # EXCELLENT, GOOD, BALANCED, OVERFITTING, UNDERFITTING


class TrainingResponse(BaseModel):
    """Training results."""
    job_id: str
    task_type: TaskType
    models_trained: List[str]
    best_model: str
    best_score: float
    training_time: float
    metrics: Dict[str, ModelMetrics]


# ─── Full Pipeline ──────────────────────────────────────────────────────
class PipelineRequest(BaseModel):
    """Request to run full AutoML pipeline."""
    target_column: str
    groq_model: Optional[str] = None
    training_config: Optional[TrainingConfig] = None
    apply_audit_fixes: bool = True
    skip_issues: Optional[List[IssueType]] = None


class PipelineResponse(BaseModel):
    """Full pipeline results."""
    job_id: str
    status: str  # completed, running, failed
    dataset_profile: Optional[DatasetProfile] = None
    audit_flags: Optional[List[DataQualityFlag]] = None
    preprocessing_log: Optional[List[PreprocessingLogEntry]] = None
    training_results: Optional[TrainingResponse] = None
    total_time: float
    error: Optional[str] = None


# ─── Job Management ─────────────────────────────────────────────────────
class JobStatus(BaseModel):
    """Job status information."""
    job_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    current_stage: str
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None


class JobResult(BaseModel):
    """Job result."""
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# ─── Predictions ────────────────────────────────────────────────────────
class PredictionRequest(BaseModel):
    """Request for predictions."""
    job_id: str
    data: List[Dict[str, Any]]


class PredictionResponse(BaseModel):
    """Prediction results."""
    predictions: List[Dict[str, Any]]
    probabilities: Optional[List[List[float]]] = None
    model_used: str


# ─── Health & Info ──────────────────────────────────────────────────────
class APIInfo(BaseModel):
    """API information."""
    name: str
    version: str
    description: str
    available_models: List[str]
    supported_formats: List[str]
    max_file_size_mb: int


class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    database: str
    groq_api: str
