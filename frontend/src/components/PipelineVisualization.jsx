import React, { useState, useEffect } from 'react'
import PipelineStep from './PipelineStep'
import { runFullPipeline, getJobStatus } from '../services/api'

const PipelineVisualization = ({ filePath, targetColumn, onComplete, onError }) => {
  const [jobId, setJobId] = useState(null)
  const [steps, setSteps] = useState({
    profile: { title: '📈 Profile Dataset', status: 'pending', progress: 0, data: null },
    audit: { title: '🔍 AI Audit', status: 'pending', progress: 0, data: null },
    preprocess: { title: '🔧 Preprocess Data', status: 'pending', progress: 0, data: null },
    features: { title: '✨ Feature Engineering', status: 'pending', progress: 0, data: null },
    train: { title: '🤖 Train Models', status: 'pending', progress: 0, data: null },
    evaluate: { title: '📊 Evaluate Results', status: 'pending', progress: 0, data: null },
  })
  const [currentStage, setCurrentStage] = useState('profile')
  const [isRunning, setIsRunning] = useState(false)
  const [finalResults, setFinalResults] = useState(null)

  // Start pipeline
  useEffect(() => {
    const startPipeline = async () => {
      setIsRunning(true)
      try {
        const response = await runFullPipeline(filePath, targetColumn, {
          applyFixes: true,
          models: ['xgboost', 'random_forest', 'gradient_boosting'],
          cvFolds: 5,
          nIter: 15,
        })
        setJobId(response.data.job_id)
        console.log('Pipeline started with job ID:', response.data.job_id)
      } catch (error) {
        onError('Failed to start pipeline: ' + error.message)
        setIsRunning(false)
      }
    }

    startPipeline()
  }, [filePath, targetColumn])

  // Poll job status
  useEffect(() => {
    if (!jobId || !isRunning) return

    const pollInterval = setInterval(async () => {
      try {
        const response = await getJobStatus(jobId)
        const job = response.data

        // Update current stage
        const stageMap = {
          'profile': 'profile',
          'audit': 'audit',
          'preprocess': 'preprocess',
          'features': 'features',
          'train': 'train',
          'evaluate': 'evaluate',
        }

        const current = stageMap[job.current_stage] || 'profile'
        setCurrentStage(current)

        // Update step status
        const newSteps = { ...steps }
        
        // Mark completed steps
        Object.keys(stageMap).forEach((stage) => {
          const stepKey = stageMap[stage]
          if (job.completed_stages.includes(stage)) {
            newSteps[stepKey].status = 'completed'
            newSteps[stepKey].progress = 100
          }
        })

        // Mark current step as running
        if (job.status === 'running') {
          newSteps[current].status = 'running'
          newSteps[current].progress = job.progress
        }

        setSteps(newSteps)

        // Handle completion
        if (job.status === 'completed') {
          newSteps[current].status = 'completed'
          newSteps[current].progress = 100
          setSteps(newSteps)
          setIsRunning(false)
          setFinalResults(job.result)
          onComplete(job.result)
          clearInterval(pollInterval)
        }

        // Handle failure
        if (job.status === 'failed') {
          newSteps[current].status = 'error'
          setSteps(newSteps)
          onError(job.error_message || 'Pipeline failed')
          setIsRunning(false)
          clearInterval(pollInterval)
        }
      } catch (error) {
        console.error('Error polling job status:', error)
      }
    }, 2000)

    return () => clearInterval(pollInterval)
  }, [jobId, isRunning])

  return (
    <div className="pipeline-visualization">
      <div className="pipeline-header">
        <h2>🚀 AutoML Pipeline in Action</h2>
        {jobId && <p className="job-id">Job ID: {jobId}</p>}
      </div>

      <div className="pipeline-container">
        <div className="steps-grid">
          {Object.entries(steps).map(([key, step]) => (
            <PipelineStep
              key={key}
              step={step}
              status={step.status}
              progress={step.progress}
              data={step.data}
              error={step.error}
            />
          ))}
        </div>
      </div>

      {finalResults && (
        <div className="pipeline-complete">
          <h3>✨ Pipeline Complete!</h3>
          <div className="results-summary">
            {finalResults.training_results && (
              <div className="result-section">
                <h4>🤖 Model Results</h4>
                <div className="metrics-table">
                  {Object.entries(finalResults.training_results.metrics || {}).map(
                    ([model, metrics]) => (
                      <div key={model} className="metric-row">
                        <span className="metric-name">{model}</span>
                        <span className="metric-value">
                          Accuracy: {(metrics.accuracy * 100).toFixed(2)}%
                        </span>
                        <span className="metric-value">
                          F1: {(metrics.f1_weighted * 100).toFixed(2)}%
                        </span>
                      </div>
                    ),
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default PipelineVisualization
