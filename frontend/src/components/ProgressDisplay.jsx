import React from 'react';

export default function ProgressDisplay({ uploadProgress, processingProgress, status }) {
    if (status === 'idle') return null;

    return (
        <div className="status-box">
            <div className="progress-item">
                <div className="progress-label">
                    <span>Upload</span>
                    <span>{uploadProgress}%</span>
                </div>
                <div className="progress-track">
                    <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
                </div>
            </div>

            {(status === 'processing' || status === 'complete') && (
                <div className="progress-item" style={{ marginTop: '1rem' }}>
                    <div className="progress-label">
                        <span>Processing</span>
                        <span>{processingProgress}%</span>
                    </div>
                    <div className="progress-track">
                        <div className="progress-fill" style={{ width: `${processingProgress}%` }}></div>
                    </div>
                </div>
            )}

            <div style={{ marginTop: '1rem', textAlign: 'center', fontStyle: 'italic' }}>
                STATUS: {status.toUpperCase()}
            </div>
        </div>
    );
}
