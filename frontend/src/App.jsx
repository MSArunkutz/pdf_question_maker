import React, { useState } from 'react';
import './App.css';
import FileUpload from './components/FileUpload';

function App() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, processing, complete, error
  const [questions, setQuestions] = useState([]);
  const [errorDetails, setErrorDetails] = useState({ message: '', requestId: '' });

  const handleFileSelect = async (selectedFile) => {
    setFile(selectedFile);
    setStatus('processing');
    setErrorDetails({ message: '', requestId: '' });
    setQuestions([]);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/api/generate-questions', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(JSON.stringify({
          message: data.error || 'Server Error',
          requestId: data.requestId || 'UNKNOWN'
        }));
      }

      setQuestions(data.questions);
      setStatus('complete');

    } catch (err) {
      console.error("Upload failed", err);
      let errMsg = "Network or Unknown Error";
      let reqId = "N/A";

      try {
        const parsed = JSON.parse(err.message);
        errMsg = parsed.message;
        reqId = parsed.requestId;
      } catch (e) {
        if (err instanceof TypeError && err.message === "Failed to fetch") {
          errMsg = "Could not connect to backend server";
        } else {
          errMsg = err.message || "Unknown Error";
        }
      }

      setErrorDetails({ message: errMsg, requestId: reqId });
      setStatus('error');
    }
  };

  const handleReset = () => {
    setFile(null);
    setStatus('idle');
    setQuestions([]);
    setErrorDetails({ message: '', requestId: '' });
  };

  return (
    <div className="app-container">
      <div className="main-card">
        <h1 className="app-title">PDF Q&A GEN</h1>

        {status === 'idle' && (
          <FileUpload onFileSelect={handleFileSelect} disabled={false} />
        )}

        {status === 'processing' && (
          <div className="status-container">
            <div className="spinner"></div>
            <p>Analyzing PDF & Generating Questions...</p>
            {file && <small>File: {file.name}</small>}
          </div>
        )}

        {status === 'error' && (
          <div className="error-container" style={{ color: '#ff6b6b', textAlign: 'center' }}>
            <h3>Error Processing Request</h3>
            <p>{errorDetails.message}</p>
            <small style={{ opacity: 0.7 }}>Request ID: {errorDetails.requestId}</small>
            <br />
            <button onClick={handleReset} style={{ marginTop: '1rem', padding: '0.5rem 1rem' }}>Try Again</button>
          </div>
        )}

        {status === 'complete' && (
          <div className="results-container">
            <h3>Generated Questions</h3>
            <p className="source-filename" style={{ fontSize: '0.9rem', color: 'var(--text-dim)', marginBottom: '1.5rem', textAlign: 'left' }}>
              Questions Generated from file : <strong>{file?.name}</strong>
            </p>
            <ul style={{ textAlign: 'left', marginBottom: '1rem' }}>
              {questions.map((q, idx) => (
                <li key={idx} style={{ marginBottom: '0.5rem' }}>{q}</li>
              ))}
            </ul>
            <div className="action-buttons">
              <button
                onClick={handleReset}
                className="secondary-btn"
              >
                Process Another PDF
              </button>

              <button
                className="secondary-btn"
                onClick={() => {
                  const blob = new Blob([JSON.stringify(questions, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'questions.json';
                  a.click();
                }}
              >
                Download JSON
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
