#!/usr/bin/env bash
# cURL Examples for AutoML Backend API
# Replace localhost:8000 with your server URL if different

BASE_URL="http://localhost:8000"

echo "═══════════════════════════════════════════════════════════════"
echo "AutoML Backend API - cURL Examples"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ─── Health & Info ────────────────────────────────────────────────
echo "1. CHECK API HEALTH"
echo "─────────────────────────────────────────────────────────────"
echo "curl $BASE_URL/health | jq"
echo ""

echo "2. GET API INFO"
echo "─────────────────────────────────────────────────────────────"
echo "curl $BASE_URL/info | jq"
echo ""

# ─── File Upload ──────────────────────────────────────────────────
echo "3. UPLOAD DATASET"
echo "─────────────────────────────────────────────────────────────"
echo "curl -F 'file=@data.csv' -F 'target_column=target' \\"
echo "  $BASE_URL/upload | jq"
echo ""
echo "# Note: Replace data.csv with your actual file"
echo ""

# ─── Dataset Profile ─────────────────────────────────────────────
echo "4. PROFILE DATASET"
echo "─────────────────────────────────────────────────────────────"
echo "curl -X POST \\"
echo "  \"$BASE_URL/pipeline/profile?file_path=uploads/data.csv&target_column=target\" | jq"
echo ""
echo "# Returns: Statistical profile, nulls, target type, balance"
echo ""

# ─── AI Audit ─────────────────────────────────────────────────────
echo "5. RUN AI AUDIT"
echo "─────────────────────────────────────────────────────────────"
echo "curl -X POST \\"
echo "  \"$BASE_URL/pipeline/audit?file_path=uploads/data.csv&target_column=target\" | jq"
echo ""
echo "# Returns: Data quality flags with severity and fixes"
echo "# Note: Requires GROQ_API_KEY in .env"
echo ""

# ─── Preprocessing ────────────────────────────────────────────────
echo "6. PREPROCESS DATASET"
echo "─────────────────────────────────────────────────────────────"
echo "curl -X POST \\"
echo "  \"$BASE_URL/pipeline/preprocess?file_path=uploads/data.csv&target_column=target\" | jq"
echo ""
echo "# Returns: Log of preprocessing steps applied"
echo ""

# ─── Train Models ─────────────────────────────────────────────────
echo "7. TRAIN MODELS"
echo "─────────────────────────────────────────────────────────────"
echo "curl -X POST \\"
echo "  \"$BASE_URL/pipeline/train?file_path=uploads/data.csv&target_column=target&models=logistic_regression,random_forest,xgboost\" | jq"
echo ""
echo "# Returns: Training results with metrics for each model"
echo ""

# ─── Full Pipeline ────────────────────────────────────────────────
echo "8. RUN FULL PIPELINE (ASYNC)"
echo "─────────────────────────────────────────────────────────────"
echo "JOB_ID=\$(curl -X POST \\
  -H 'Content-Type: application/json' \\
  -d '{
    \"file_path\": \"uploads/data.csv\",
    \"target_column\": \"target\",
    \"apply_audit_fixes\": true,
    \"training_config\": {
      \"models\": [\"xgboost\", \"random_forest\"],
      \"cv_folds\": 5,
      \"n_iter\": 15
    }
  }' \\
  $BASE_URL/pipeline/run | jq -r .job_id)"
echo ""
echo "# Returns: Job ID for tracking"
echo ""

# ─── Check Job Status ─────────────────────────────────────────────
echo "9. CHECK JOB STATUS"
echo "─────────────────────────────────────────────────────────────"
echo "# After running pipeline, check progress:"
echo "curl \"$BASE_URL/jobs/\$JOB_ID\" | jq"
echo ""
echo "# Watch progress in real-time:"
echo "watch -n 2 'curl \"$BASE_URL/jobs/\$JOB_ID\" | jq .progress'"
echo ""

# ─── Get Job Results ──────────────────────────────────────────────
echo "10. GET JOB RESULTS"
echo "─────────────────────────────────────────────────────────────"
echo "curl \"$BASE_URL/jobs/\$JOB_ID\" | jq .result"
echo ""
echo "# Or save to file:"
echo "curl \"$BASE_URL/jobs/\$JOB_ID\" | jq .result > results.json"
echo ""

# ─── Make Predictions ─────────────────────────────────────────────
echo "11. MAKE PREDICTIONS"
echo "─────────────────────────────────────────────────────────────"
echo "curl -X POST \\
  -H 'Content-Type: application/json' \\
  -d '{
    \"job_id\": \"550e8400-e29b-41d4-a716-446655440000\",
    \"data\": [
      {
        \"age\": 45,
        \"sex\": 1,
        \"cp\": 3,
        \"trestbps\": 140
      }
    ]
  }' \\
  $BASE_URL/predict | jq"
echo ""
echo "# Returns: Predictions and probabilities"
echo ""

# ─── List All Jobs ────────────────────────────────────────────────
echo "12. LIST ALL JOBS"
echo "─────────────────────────────────────────────────────────────"
echo "curl \"$BASE_URL/jobs\" | jq"
echo ""
echo "# Returns: All jobs with status, progress, timestamps"
echo ""

# ─── Advanced Examples ────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════════"
echo "ADVANCED EXAMPLES"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "A. FILTER PIPELINE RESULTS"
echo "─────────────────────────────────────────────────────────────"
echo "# Get only high-severity issues:"
echo "curl \"$BASE_URL/jobs/\$JOB_ID\" | jq '.result.audit_flags[] | select(.severity==\"high\")'"
echo ""

echo "B. COMPARE MODEL METRICS"
echo "─────────────────────────────────────────────────────────────"
echo "# Show best models:"
echo "curl \"$BASE_URL/jobs/\$JOB_ID\" | jq '.result.training_results.metrics | to_entries | sort_by(-.value.f1_weighted) | .[0:3]'"
echo ""

echo "C. EXPORT RESULTS"
echo "─────────────────────────────────────────────────────────────"
echo "# Export as CSV:"
echo "curl \"$BASE_URL/jobs/\$JOB_ID\" | jq -r '.result.training_results.metrics | to_entries[] | [.key, .value.accuracy, .value.f1_weighted, .value.cv_mean] | @csv' > results.csv"
echo ""

echo "D. BATCH MULTIPLE UPLOADS"
echo "─────────────────────────────────────────────────────────────"
echo "# Upload multiple files:"
echo "for file in data*.csv; do"
echo "  curl -F \"file=@\$file\" -F 'target_column=target' $BASE_URL/upload"
echo "done"
echo ""

echo "E. CONTINUOUS MONITORING"
echo "─────────────────────────────────────────────────────────────"
echo "# Monitor job until completion:"
echo "JOB_ID='550e8400-e29b-41d4-a716-446655440000'"
echo "while true; do"
echo "  STATUS=\$(curl -s \"$BASE_URL/jobs/\$JOB_ID\" | jq -r .status)"
echo "  PROGRESS=\$(curl -s \"$BASE_URL/jobs/\$JOB_ID\" | jq .progress)"
echo "  echo \"Status: \$STATUS (\$PROGRESS%)\""
echo "  [ \"\$STATUS\" != \"running\" ] && break"
echo "  sleep 5"
echo "done"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "USEFUL TOOLS"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "• Interactive API Docs:  http://localhost:8000/docs"
echo "• Alternative Docs:       http://localhost:8000/redoc"
echo "• OpenAPI Schema:         http://localhost:8000/openapi.json"
echo "• Format JSON output:     pipe to '| jq'"
echo "• Pretty print:           pipe to '| jq .'"
echo "• Pretty print to file:   pipe to '| jq > file.json'"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "TIPS"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. Save commonly used commands in a script"
echo "2. Use 'jq' for JSON filtering and transformation"
echo "3. Pipe results to 'tee' to save and display"
echo "4. Use 'watch' to monitor changes in real-time"
echo "5. Check .env to ensure GROQ_API_KEY is set"
echo "6. Monitor logs in logs/ directory during long operations"
echo ""
