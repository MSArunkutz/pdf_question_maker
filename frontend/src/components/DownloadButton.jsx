import React from 'react';

export default function DownloadButton({ disabled }) {
    const handleDownload = () => {
        const data = {
            questions: [
                { id: 1, question: "What is the main topic of the PDF?", answer: "The PDF discusses..." },
                { id: 2, question: "Explain the key concept.", answer: "The key concept is..." }
            ]
        };
        const jsonString = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = 'questions.json';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <button
            className="primary-btn"
            onClick={handleDownload}
            disabled={disabled}
            style={{ width: '100%' }}
        >
            {disabled ? 'WAITING FOR PROCESS...' : 'DOWNLOAD JSON'}
        </button>
    );
}
