import React, { useState, useEffect } from 'react'
import Upload from './components/Upload'
import PipelineVisualization from './components/PipelineVisualization'
import { checkHealth } from './services/api'
import './styles/App.css'

function App() {
  const [apiReady, setApiReady] = useState(false)
  const [error, setError] = useState(null)
  const [uploadedData, setUploadedData] = useState(null)
  const [pipelineComplete, setPipelineComplete] = useState(false)
  const [results, setResults] = useState(null)

  // Check backend health on mount
  useEffect(() => {
    const checkAPI = async () => {
      try {
        const response = await checkHealth()
        setApiReady(true)
        console.log('✅ Backend API is healthy')
      } catch (err) {
        setError('❌ Cannot connect to backend. Make sure the API is running on http://localhost:8000')
        console.error('API health check failed:', err)
      }
    }

    checkAPI()
  }, [])

  const handleUploadSuccess = (data) => {
    setUploadedData(data)
    setError(null)
    setPipelineComplete(false)
  }

  const handlePipelineComplete = (results) => {
    setPipelineComplete(true)
    setResults(results)
  }

  const handleError = (errorMsg) => {
    setError(errorMsg)
  }

  const handleReset = () => {
    setUploadedData(null)
    setPipelineComplete(false)
    setResults(null)
    setError(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>🤖 AutoML Pipeline</h1>
          <p>Intelligent Machine Learning Automation</p>
        </div>
        <div className="api-status">
          {apiReady ? (
            <span className="status-badge status-ok">✅ API Connected</span>
          ) : (
            <span className="status-badge status-error">❌ API Disconnected</span>
          )}
        </div>
      </header>

      <main className="app-main">
        {error && (
          <div className="error-banner">
            <div className="error-content">
              <span className="error-icon">⚠️</span>
              <div>
                <strong>Error:</strong> {error}
              </div>
              <button onClick={() => setError(null)} className="btn-close">✕</button>
            </div>
          </div>
        )}

        {!apiReady ? (
          <div className="connection-error">
            <h2>🔌 Backend Connection Required</h2>
            <p>Please make sure your FastAPI backend is running:</p>
            <code>uvicorn main:app --reload</code>
            <p style={{ marginTop: '1rem' }}>The backend should be available at:</p>
            <code>http://localhost:8000</code>
          </div>
        ) : !uploadedData ? (
          <Upload
            onUploadSuccess={handleUploadSuccess}
            onError={handleError}
          />
        ) : !pipelineComplete ? (
          <div className="pipeline-section">
            <PipelineVisualization
              filePath={uploadedData.filePath}
              targetColumn={uploadedData.targetColumn}
              onComplete={handlePipelineComplete}
              onError={handleError}
            />
          </div>
        ) : (
          <div className="results-section">
            <div className="results-header">
              <h2>🎉 Pipeline Complete!</h2>
              <button onClick={handleReset} className="btn btn-secondary">
                ↻ Process Another Dataset
              </button>
            </div>

            {results && (
              <div className="results-content">
                {/* Profile Results */}
                {results.profile && (
                  <div className="result-card">
                    <h3>📈 Dataset Profile</h3>
                    <div className="result-details">
                      <p><strong>Rows:</strong> {results.profile.rows}</p>
                      <p><strong>Columns:</strong> {results.profile.columns}</p>
                      <p><strong>Target Type:</strong> {results.profile.target_type}</p>
                      {results.profile.target_balance && (
                        <p><strong>Target Balance:</strong> {results.profile.target_balance}</p>
                      )}
                    </div>
                  </div>
                )}

                {/* Audit Results */}
                {results.audit_flags && results.audit_flags.length > 0 && (
                  <div className="result-card">
                    <h3>🔍 Data Quality Audit</h3>
                    <div className="flags-list">
                      {results.audit_flags.map((flag, idx) => (
                        <div
                          key={idx}
                          className={`flag-item severity-${flag.severity}`}
                        >
                          <span className="flag-type">{flag.issue_type}</span>
                          <p>{flag.description}</p>
                          {flag.recommendation && (
                            <small>{flag.recommendation}</small>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Training Results */}
                {results.training_results && (
                  <div className="result-card">
                    <h3>🤖 Model Performance</h3>
                    <div className="models-grid">
                      {Object.entries(results.training_results.metrics || {}).map(
                        ([model, metrics]) => (
                          <div key={model} className="model-card">
                            <h4>{model}</h4>
                            <div className="metrics-display">
                              <div className="metric">
                                <span className="metric-label">Accuracy</span>
                                <span className="metric-bar">
                                  <div
                                    className="metric-fill"
                                    style={{
                                      width: `${metrics.accuracy * 100}%`,
                                    }}
                                  ></div>
                                </span>
                                <span className="metric-value">
                                  {(metrics.accuracy * 100).toFixed(2)}%
                                </span>
                              </div>
                              <div className="metric">
                                <span className="metric-label">F1 Score</span>
                                <span className="metric-bar">
                                  <div
                                    className="metric-fill"
                                    style={{
                                      width: `${metrics.f1_weighted * 100}%`,
                                    }}
                                  ></div>
                                </span>
                                <span className="metric-value">
                                  {(metrics.f1_weighted * 100).toFixed(2)}%
                                </span>
                              </div>
                              {metrics.generalization_status && (
                                <div className="generalization">
                                  <span className="label">Status:</span>
                                  <span className={`status ${metrics.generalization_status.toLowerCase()}`}>
                                    {metrics.generalization_status}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>AutoML Pipeline v1.0 | Powered by FastAPI & React</p>
      </footer>
    </div>
  )
}

export default App
