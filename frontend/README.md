# AutoML Frontend - React Application

## 🎨 Overview

This is a modern React frontend for the AutoML backend. It provides an interactive interface for:
- Uploading datasets
- Watching the AI pipeline work through each step
- Monitoring progress in real-time
- Viewing results and model performance metrics

## 🏗️ Project Structure

```
frontend/
├── public/                    # Static assets
├── src/
│   ├── components/           # React components
│   │   ├── Upload.jsx       # File upload interface
│   │   ├── PipelineStep.jsx # Individual pipeline step display
│   │   └── PipelineVisualization.jsx # Full pipeline orchestration
│   ├── services/
│   │   └── api.js           # Backend API client
│   ├── styles/
│   │   └── App.css          # Global styles
│   ├── App.jsx              # Main application component
│   └── main.jsx             # React entry point
├── index.html               # HTML template
├── vite.config.js          # Vite configuration
├── package.json            # Dependencies
└── README.md               # This file
```

## 📋 Prerequisites

- **Node.js** 16.0.0 or higher
- **npm** 8.0.0 or higher
- **Backend** running on http://localhost:8000

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure API Connection

```bash
cp .env.example .env
# Edit .env if your backend is on a different URL
```

### 3. Start Development Server

```bash
npm run dev
```

The frontend will be available at: **http://localhost:3000**

### 4. Using Startup Scripts

**Linux/Mac:**
```bash
bash quickstart.sh
```

**Windows:**
```bash
quickstart.bat
```

## 🎯 Features

### Upload Interface
- Drag-and-drop file upload
- Support for CSV, Excel, and JSON files
- Target column selection
- File size validation (max 100MB)

### Pipeline Visualization
Shows the AI system working through 6 steps:

1. **📈 Profile Dataset** - Statistical analysis and data profiling
2. **🔍 AI Audit** - Data quality assessment using Groq AI
3. **🔧 Preprocess Data** - Automated cleaning and preprocessing
4. **✨ Feature Engineering** - Automatic feature creation
5. **🤖 Train Models** - Multiple model training with hyperparameter tuning
6. **📊 Evaluate Results** - Model performance analysis

### Real-Time Progress Tracking
- Live progress bars for each step
- Current stage highlighting
- Detailed error reporting
- Job ID tracking

### Results Display
- Model performance metrics (accuracy, F1 score)
- Generalization status (Excellent/Good/Balanced/Overfitting/Underfitting)
- Data quality flags and recommendations
- Comprehensive metrics visualization

## 🔌 API Integration

The frontend communicates with the FastAPI backend through:

- **Upload**: `/upload` - File upload and preview
- **Profile**: `/pipeline/profile` - Dataset statistics
- **Audit**: `/pipeline/audit` - AI-powered audit
- **Preprocess**: `/pipeline/preprocess` - Data cleaning
- **Train**: `/pipeline/train` - Model training
- **Run**: `/pipeline/run` - Full pipeline (async)
- **Jobs**: `/jobs/{id}` - Job status tracking

## 🛠️ Build & Deployment

### Development Build

```bash
npm run dev
```

### Production Build

```bash
npm run build
```

This creates an optimized build in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## 📊 Component Overview

### Upload.jsx
- File input with drag-and-drop
- Target column specification
- File validation and preview
- Calls `uploadDataset()` API

### PipelineVisualization.jsx
- Orchestrates the full pipeline
- Polls job status every 2 seconds
- Updates step progress dynamically
- Displays final results

### PipelineStep.jsx
- Individual step display
- Status icons (✅ completed, ⏳ running, etc.)
- Progress bar visualization
- Details collapse section

### api.js
- Axios-based API client
- All endpoint functions
- Automatic error handling
- Base URL configuration

## 🎨 Styling

The frontend uses a custom CSS design with:
- **Color scheme**: Blue primary color with gradients
- **Responsive layout**: Mobile-first design
- **Dark mode ready**: CSS variables for easy theming
- **Accessibility**: Semantic HTML and ARIA labels

### CSS Variables

Key colors and styles defined in `src/styles/App.css`:

```css
--primary-color: #2563eb
--success-color: #10b981
--error-color: #ef4444
--warning-color: #f59e0b
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```env
REACT_APP_API_URL=http://localhost:8000
```

### API Configuration

Edit `src/services/api.js` to change:
- Base URL
- Request headers
- Timeout settings
- Retry logic

## 📱 Responsive Design

The UI is fully responsive:
- **Mobile**: Single column layout
- **Tablet**: 2-column grid
- **Desktop**: Multi-column adaptive layout

## 🐛 Troubleshooting

### Backend Connection Error
```
❌ Cannot connect to backend
```

**Solution**: Make sure the backend is running:
```bash
cd ../automl-backend
uvicorn main:app --reload
```

### CORS Error
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution**: The backend includes CORS configuration. Make sure:
1. Backend is running with CORS middleware enabled
2. Frontend URL is in allowed origins
3. Check `http://localhost:3000` is not blocked

### Dependencies Installation Error

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 🚀 Production Deployment

### Build Optimization
```bash
npm run build
```

### Serve Static Files
Use any static file server (nginx, apache, or Node.js):

```bash
# Using http-server
npx http-server dist/
```

### Docker Deployment

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## 📚 API Examples

### Upload Dataset
```javascript
const response = await uploadDataset(file, 'target_column');
// Returns: { file_path, preview, profile }
```

### Run Full Pipeline
```javascript
const response = await runFullPipeline(filePath, targetColumn, config);
// Returns: { job_id, status }
```

### Check Job Status
```javascript
const response = await getJobStatus(jobId);
// Returns: { status, progress, current_stage, result }
```

## 🤝 Contributing

To contribute to the frontend:

1. Create a feature branch: `git checkout -b feature/amazing-feature`
2. Make your changes
3. Test thoroughly
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open a pull request

## 📄 License

MIT License - Same as main project

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the backend BACKEND_README.md
3. Check browser console for errors (F12)
4. Verify backend is running and accessible

## 🎯 Next Steps

- [ ] Add authentication/login
- [ ] Add dataset preview in table format
- [ ] Add real-time WebSocket updates
- [ ] Add export results to CSV/JSON
- [ ] Add prediction interface
- [ ] Add model comparison charts
- [ ] Add data visualization dashboard
- [ ] Add backend logs viewer

## 📈 Performance Tips

- Use `npm run build` for production
- Enable gzip compression on the server
- Cache static assets with long expiration
- Use a CDN for asset delivery
- Monitor bundle size with `npm run analyze` (if configured)

## 🔒 Security

- Never commit `.env` with sensitive data
- Use HTTPS in production
- Validate file uploads on backend (already implemented)
- Use environment variables for API URLs
- Implement CSRF protection if needed

---

**Built with React 18, Vite, and Axios**
