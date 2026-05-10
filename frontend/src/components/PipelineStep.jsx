import React from 'react'

const PipelineStep = ({ step, status, progress, data, error }) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return '✅'
      case 'running':
        return '⏳'
      case 'pending':
        return '⭕'
      case 'error':
        return '❌'
      default:
        return '📋'
    }
  }

  const getStatusClass = () => {
    return `step-${status}`
  }

  return (
    <div className={`pipeline-step ${getStatusClass()}`}>
      <div className="step-header">
        <span className="step-icon">{getStatusIcon()}</span>
        <h3 className="step-title">{step.title}</h3>
        {progress !== undefined && (
          <span className="step-progress">{progress}%</span>
        )}
      </div>

      {step.description && (
        <p className="step-description">{step.description}</p>
      )}

      {status === 'running' && (
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress || 0}%` }}></div>
        </div>
      )}

      {error && (
        <div className="step-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {data && (
        <div className="step-results">
          <details>
            <summary>📊 View Details</summary>
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  )
}

export default PipelineStep
