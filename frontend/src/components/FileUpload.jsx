import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

const MAX_SIZE = 10 * 1024 * 1024; // 10MB

export default function FileUpload({ onFileSelect, disabled }) {
    const onDrop = useCallback(acceptedFiles => {
        if (acceptedFiles?.length > 0) {
            onFileSelect(acceptedFiles[0]);
        }
    }, [onFileSelect]);

    const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
        onDrop,
        accept: { 'application/pdf': ['.pdf'] },
        maxSize: MAX_SIZE,
        multiple: false,
        disabled
    });

    const fileError = fileRejections.length > 0 ? fileRejections[0].errors[0] : null;

    return (
        <div className="file-upload-section">
            <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
                <input {...getInputProps()} />
                {isDragActive ? (
                    <p>DROP THE PDF HERE...</p>
                ) : (
                    <p>DRAG & DROP PDF HERE<br />OR CLICK TO SELECT<br /><br />(MAX 10MB)</p>
                )}
            </div>
            {fileError && (
                <div style={{
                    color: '#ff6b6b',
                    marginTop: '1rem',
                    background: 'rgba(255,107,107,0.1)',
                    border: '1px solid rgba(255,107,107,0.2)',
                    padding: '0.75rem',
                    borderRadius: '8px',
                    fontSize: '0.9rem'
                }}>
                    ERROR: {fileError.code === 'file-too-large' ? 'FILE TOO LARGE (>10MB)' : 'INVALID FILE FORMAT'}
                </div>
            )}
        </div>
    );
}
