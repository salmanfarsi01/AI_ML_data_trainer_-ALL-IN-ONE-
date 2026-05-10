import React, { useState } from 'react'
import { uploadDataset } from '../services/api'

const Upload = ({ onUploadSuccess, onError }) => {
  const [file, setFile] = useState(null)
  const [targetColumn, setTargetColumn] = useState('')
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState(null)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    setFile(selectedFile)
    if (selectedFile) {
      setPreview(`📄 ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(2)} KB)`)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file || !targetColumn) {
      onError('Please select a file and enter target column')
      return
    }

    setLoading(true)
    try {
      const response = await uploadDataset(file, targetColumn)
      setFile(null)
      setTargetColumn('')
      setPreview(null)
      onUploadSuccess({
        filePath: response.data.file_path,
        targetColumn: targetColumn,
        preview: response.data.preview,
        profile: response.data.profile,
      })
    } catch (error) {
      onError(error.response?.data?.detail || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="upload-container">
      <div className="upload-header">
        <h2>📊 Upload Your Dataset</h2>
        <p>Start your AutoML journey - upload a CSV or Excel file</p>
      </div>

      <form onSubmit={handleSubmit} className="upload-form">
        <div className="form-group">
          <label htmlFor="file">Select Dataset File</label>
          <input
            id="file"
            type="file"
            accept=".csv,.xlsx,.xls,.json"
            onChange={handleFileChange}
            className="file-input"
            disabled={loading}
          />
          {preview && <div className="file-preview">{preview}</div>}
        </div>

        <div className="form-group">
          <label htmlFor="target">Target Column Name</label>
          <input
            id="target"
            type="text"
            placeholder="e.g., target, label, price, outcome"
            value={targetColumn}
            onChange={(e) => setTargetColumn(e.target.value)}
            className="text-input"
            disabled={loading}
          />
          <small>The column you want to predict</small>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || !file}
        >
          {loading ? '⏳ Uploading...' : '🚀 Upload & Analyze'}
        </button>
      </form>

      <div className="upload-info">
        <h3>Supported Formats</h3>
        <ul>
          <li>CSV (.csv)</li>
          <li>Excel (.xlsx, .xls)</li>
          <li>JSON (.json)</li>
        </ul>
        <p>Maximum file size: 100 MB</p>
      </div>
    </div>
  )
}

export default Upload
