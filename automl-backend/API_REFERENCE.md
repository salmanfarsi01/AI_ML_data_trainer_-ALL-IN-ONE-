# AutoML REST API Reference

**Base URL:** `http://localhost:8000`

---

## Overview

The AutoML API provides 8 endpoints mapping to the complete ML pipeline stages from `auto_ai.py`.

---

## 1️⃣ Upload Dataset & Profile

### `POST /api/upload/`

Upload a tabular dataset (CSV, Excel, JSON). System automatically profiles it.

**Request:**
```http
POST /api/upload/ HTTP/1.1
Content-Type: multipart/form-data

file: <binary>
target_col: "target"  [optional]
```

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "titanic.csv",
  "shape": [891, 12],
  "preview": [
    {"PassengerId": 1, "Survived": 0, "Pclass": 3, ...},
    {"PassengerId": 2, "Survived": 1, "Pclass": 1, ...}
  ],
  "columns": ["PassengerId", "Survived", "Pclass", ...],
  "dtypes": {
    "PassengerId": "int64",
    "Survived": "int64",
    "Name": "object"
  },
  "profile": {
    "shape": {"rows": 891, "cols": 12},
    "global": {
      "duplicate_rows": 0,
      "duplicate_pct": 0.0,
      "total_null_cells": 177,
      "total_null_pct": 1.66,
      "target_col": "Survived",
      "target_type": "binary",
      "target_balance": {"0": 0.6162, "1": 0.3838}
    },
    "columns": {
      "PassengerId": {
        "dtype": "int64",
        "kind": "numeric",
        "null_count": 0,
        "null_pct": 0.0,
        "mean": 446.0,
        "std": 257.35,
        ...
      },
      "Name": {
        "dtype": "object",
        "kind": "categorical",
        "unique_count": 891,
        "cardinality_ratio": 1.0,
        "top_values": {"Braund, Mr. Owen Harris": 1, ...}
      }
    }
  }
}
```

**Error:** `400 Bad Request`
```json
{
  "detail": "Unsupported file type '.txt'. Allowed: {'.csv', '.xlsx', '.xls', '.json'}"
}
```

---

## 2️⃣ Run AI Audit

### `POST /api/audit/{session_id}`

Send the dataset profile to Groq API for data quality assessment.

**Request:**
```http
POST /api/audit/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Content-Type: application/json
```

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "flags": [
    {
      "id": "flag_000",
      "column": "Age",
      "issue_type": "missing_values",
      "severity": "high",
      "detail": "177 null values (19.9%) will bias age-based predictions and reduce model accuracy",
      "recommended_fix": "Impute with KNN (k=5) to preserve age distribution",
      "auto_fixable": true
    },
    {
      "id": "flag_001",
      "column": "Cabin",
      "issue_type": "high_cardinality",
      "severity": "medium",
      "detail": "148 unique values with 77% missing — too sparse for meaningful signal",
      "recommended_fix": "Drop column (no predictive value) or encode as binary (has_cabin)",
      "auto_fixable": true
    },
    {
      "id": "flag_002",
      "column": "global",
      "issue_type": "class_imbalance",
      "severity": "medium",
      "detail": "Target distribution is 62% class 0 vs 38% class 1 — model may overfit to majority",
      "recommended_fix": "Apply SMOTE on training set (after split) to balance samples",
      "auto_fixable": true
    }
  ],
  "cost_estimate": {
    "estimated_input_tokens": 587,
    "estimated_output_tokens": 421,
    "estimated_cost_usd": 0.00
  }
}
```

**Error:** `404 Not Found`
```json
{
  "detail": "Session not found"
}
```

---

## 3️⃣ Confirm Flags

### `POST /api/audit/{session_id}/confirm`

User selects which flags to apply (approval step).

**Request:**
```http
POST /api/audit/550e8400-e29b-41d4-a716-446655440000/confirm HTTP/1.1
Content-Type: application/json

{
  "confirmed_flag_ids": ["flag_000", "flag_002"]
}
```

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "confirmed_count": 2,
  "total_flags": 3,
  "confirmed_fixes": [
    {
      "id": "flag_000",
      "column": "Age",
      "issue_type": "missing_values",
      "recommended_fix": "Impute with KNN (k=5)"
    },
    {
      "id": "flag_002",
      "column": "global",
      "issue_type": "class_imbalance",
      "recommended_fix": "Apply SMOTE on training set"
    }
  ],
  "next_step": "POST /api/preprocess/{session_id}"
}
```

---

## 4️⃣ Apply Preprocessing Fixes

### `POST /api/preprocess/{session_id}`

Apply all confirmed fixes: imputation, outlier clipping, encoding, scaling.

**Request:**
```http
POST /api/preprocess/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Content-Type: application/json

{
  "scaling_method": "standard",
  "encode_remaining_cats": true
}
```

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "original_shape": {"rows": 891, "cols": 12},
  "clean_shape": {"rows": 891, "cols": 16},
  "steps_applied": 8,
  "log": [
    "Age: nulls imputed using knn",
    "Fare: outliers clipped (IQR)",
    "Sex: one-hot encoded (2 cats)",
    "Embarked: one-hot encoded (3 cats)",
    "Cabin: dropped (77% null, high sparsity)",
    "Ticket: label encoded (681 cats)",
    "Scaled 5 numeric columns using standard scaler"
  ],
  "remaining_columns": [
    "PassengerId", "Survived", "Pclass", "Age", "SibSp", "Parch",
    "Fare", "Sex_female", "Sex_male", "Embarked_C", "Embarked_Q", "Embarked_S",
    "Ticket_encoded"
  ],
  "message": "Preprocessing complete. Proceed to /api/features/{session_id}"
}
```

**Get Log:** `GET /api/preprocess/{session_id}`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "clean_shape": {"rows": 891, "cols": 16},
  "log": [...]
}
```

---

## 5️⃣ Feature Engineering & Split

### `POST /api/features/{session_id}`

Analyze feature importance, find correlations, apply PCA (optional), split train/test.

**Request:**
```http
POST /api/features/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Content-Type: application/json

{
  "use_pca": false,
  "pca_variance": 0.95,
  "test_size": 0.2,
  "selected_features": null
}
```

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_type": "classification",
  "feature_importance": [
    {
      "feature": "Sex_female",
      "importance": 0.287461,
      "cumulative": 0.2875,
      "keep_suggested": true
    },
    {
      "feature": "Pclass",
      "importance": 0.198745,
      "cumulative": 0.4862,
      "keep_suggested": true
    },
    {
      "feature": "Age",
      "importance": 0.156234,
      "cumulative": 0.6425,
      "keep_suggested": true
    }
  ],
  "high_correlation_pairs": [
    {
      "col_a": "Sex_female",
      "col_b": "Sex_male",
      "correlation": 0.9999,
      "suggestion": "Consider dropping 'Sex_male' (redundant with 'Sex_female')"
    }
  ],
  "split_info": {
    "train_rows": 712,
    "test_rows": 178,
    "train_pct": 80.0,
    "test_pct": 20.0,
    "selected_features": 12
  },
  "next_step": "POST /api/train/{session_id}",
  "message": "Feature engineering complete. Select models and train."
}
```

---

## 6️⃣ List Available Models

### `GET /api/train/{session_id}/models`

Get list of available models for this task type (classification vs regression).

**Request:**
```http
GET /api/train/550e8400-e29b-41d4-a716-446655440000/models HTTP/1.1
```

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_type": "classification",
  "available_models": [
    "logistic_regression",
    "random_forest",
    "gradient_boosting",
    "knn",
    "svm",
    "mlp",
    "xgboost",
    "lightgbm"
  ]
}
```

---

## 7️⃣ Train Models

### `POST /api/train/{session_id}`

Train selected models with hyperparameter tuning (RandomizedSearchCV).

**Request:**
```http
POST /api/train/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Content-Type: application/json

{
  "model_names": ["random_forest", "xgboost", "logistic_regression"],
  "n_iter": 20,
  "cv": 5
}
```

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "training_started": true,
  "models_requested": ["random_forest", "xgboost", "logistic_regression"],
  "results": {
    "random_forest": {
      "status": "completed",
      "best_params": {
        "n_estimators": 200,
        "max_depth": 10,
        "min_samples_split": 5
      },
      "best_score": 0.8234,
      "cv_scores": [0.8156, 0.8312, 0.8176, 0.8198, 0.8290],
      "cv_mean": 0.8226,
      "cv_std": 0.0056,
      "path": ".../550e8400_model_random_forest.joblib"
    },
    "xgboost": {
      "status": "completed",
      "best_params": {
        "n_estimators": 150,
        "learning_rate": 0.1,
        "max_depth": 5
      },
      "best_score": 0.8412,
      "cv_scores": [0.8356, 0.8498, 0.8389, 0.8401, 0.8455],
      "cv_mean": 0.8420,
      "cv_std": 0.0052,
      "path": ".../550e8400_model_xgboost.joblib"
    },
    "logistic_regression": {
      "status": "completed",
      "best_params": {"C": 1.0, "solver": "lbfgs"},
      "best_score": 0.7934,
      "cv_scores": [0.7856, 0.8012, 0.7923, 0.7987, 0.8001],
      "cv_mean": 0.7956,
      "cv_std": 0.0062,
      "path": ".../550e8400_model_logistic_regression.joblib"
    }
  },
  "next_step": "POST /api/evaluate/{session_id}/{model_name}",
  "message": "Training complete. Select a model for evaluation."
}
```

---

## 8️⃣ Evaluate Model

### `POST /api/evaluate/{session_id}/{model_name}`

Get full evaluation metrics, ROC curve, confusion matrix, feature importance.

**Request:**
```http
POST /api/evaluate/550e8400-e29b-41d4-a716-446655440000/random_forest HTTP/1.1
Content-Type: application/json
```

**Response:** `200 OK`
```json
{
  "model_name": "random_forest",
  "task_type": "classification",
  "metrics": {
    "accuracy": 0.8315,
    "f1_weighted": 0.8128,
    "precision_weighted": 0.8267,
    "recall_weighted": 0.8315,
    "roc_auc": 0.8934
  },
  "roc_curve": {
    "type": "binary",
    "fpr": [0.0, 0.0123, 0.0247, ..., 1.0],
    "tpr": [0.0, 0.1234, 0.2891, ..., 1.0],
    "auc": 0.8934
  },
  "confusion_matrix": {
    "matrix": [[115, 12], [18, 33]],
    "labels": ["0", "1"]
  },
  "cv_curve": {
    "folds": [0.8156, 0.8312, 0.8176, 0.8198, 0.8290],
    "mean": 0.8226,
    "std": 0.0056
  },
  "feature_importance": [
    {"feature": "Sex_female", "importance": 0.287461, "cumulative": 0.2875},
    {"feature": "Pclass", "importance": 0.198745, "cumulative": 0.4862},
    {"feature": "Age", "importance": 0.156234, "cumulative": 0.6425},
    {"feature": "Fare", "importance": 0.134567, "cumulative": 0.7771}
  ],
  "classification_report": {
    "0": {"precision": 0.8651, "recall": 0.9053, "f1-score": 0.8848},
    "1": {"precision": 0.7333, "recall": 0.6471, "f1-score": 0.6875},
    "weighted avg": {"precision": 0.8267, "recall": 0.8315, "f1-score": 0.8128}
  }
}
```

---

## Compare All Models

### `GET /api/evaluate/{session_id}/compare`

Compare metrics across all trained models.

**Request:**
```http
GET /api/evaluate/550e8400-e29b-41d4-a716-446655440000/compare HTTP/1.1
```

**Response:** `200 OK`
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "comparison": [
    {
      "model": "xgboost",
      "accuracy": 0.8427,
      "f1_weighted": 0.8298,
      "roc_auc": 0.9012,
      "rank": 1
    },
    {
      "model": "random_forest",
      "accuracy": 0.8315,
      "f1_weighted": 0.8128,
      "roc_auc": 0.8934,
      "rank": 2
    },
    {
      "model": "logistic_regression",
      "accuracy": 0.7898,
      "f1_weighted": 0.7634,
      "roc_auc": 0.8456,
      "rank": 3
    }
  ],
  "winner": "xgboost"
}
```

---

## Health Check

### `GET /`

Check if API is running.

**Request:**
```http
GET / HTTP/1.1
```

**Response:** `200 OK`
```json
{
  "status": "ok",
  "message": "AutoML API is running"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

Common HTTP status codes:
- `200 OK` — Success
- `400 Bad Request` — Invalid input (wrong file format, missing fields)
- `404 Not Found` — Session not found or resource doesn't exist
- `422 Unprocessable Entity` — Semantic error (target column not in data)
- `500 Internal Server Error` — Server error (Groq API down, etc.)

---

## TypeScript Client

```typescript
import {
  uploadFile,
  auditProfile,
  confirmFlags,
  preprocess,
  engineerFeatures,
  trainModels,
  evaluateModel,
  compareModels,
} from './services/apiClient';

// Usage
const { session_id, profile } = await uploadFile(csvFile, 'target');
const { flags } = await auditProfile(session_id);
const { confirmed_count } = await confirmFlags(session_id, ['flag_000', 'flag_002']);
// ... etc
```

---

## Curl Examples

### Upload
```bash
curl -X POST http://localhost:8000/api/upload/ \
  -F "file=@titanic.csv" \
  -F "target_col=Survived"
```

### Audit
```bash
curl -X POST http://localhost:8000/api/audit/550e8400-e29b-41d4-a716-446655440000
```

### Train
```bash
curl -X POST http://localhost:8000/api/train/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "model_names": ["random_forest", "xgboost"],
    "n_iter": 20,
    "cv": 5
  }'
```

### Evaluate
```bash
curl -X POST http://localhost:8000/api/evaluate/550e8400-e29b-41d4-a716-446655440000/random_forest
```

