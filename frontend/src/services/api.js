import axios from 'axios'

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Health check
export const checkHealth = () => api.get('/health')

// Get API info
export const getAPIInfo = () => api.get('/info')

// Upload dataset
export const uploadDataset = (file, targetColumn) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post(`/upload?target_column=${targetColumn}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// Profile dataset
export const profileDataset = (filePath, targetColumn) => {
  return api.post(`/pipeline/profile?file_path=${filePath}&target_column=${targetColumn}`)
}

// Audit dataset
export const auditDataset = (filePath, targetColumn) => {
  return api.post(`/pipeline/audit?file_path=${filePath}&target_column=${targetColumn}`)
}

// Preprocess dataset
export const preprocessDataset = (filePath, targetColumn) => {
  return api.post(`/pipeline/preprocess?file_path=${filePath}&target_column=${targetColumn}`)
}

// Train models
export const trainModels = (filePath, targetColumn, models = [], cvFolds = 5) => {
  const modelList = models.length > 0 ? models.join(',') : 'logistic_regression,random_forest,xgboost'
  return api.post(
    `/pipeline/train?file_path=${filePath}&target_column=${targetColumn}&models=${modelList}&cv_folds=${cvFolds}`,
  )
}

// Run full pipeline
export const runFullPipeline = (filePath, targetColumn, config = {}) => {
  return api.post('/pipeline/run', {
    file_path: filePath,
    target_column: targetColumn,
    apply_audit_fixes: config.applyFixes !== false,
    training_config: {
      models: config.models || ['xgboost', 'random_forest', 'gradient_boosting'],
      cv_folds: config.cvFolds || 5,
      n_iter: config.nIter || 15,
    },
  })
}

// Get job status
export const getJobStatus = (jobId) => api.get(`/jobs/${jobId}`)

// Get all jobs
export const getAllJobs = () => api.get('/jobs')

// Make prediction
export const makePrediction = (jobId, data) => {
  return api.post('/predict', {
    job_id: jobId,
    data: data,
  })
}

export default api
