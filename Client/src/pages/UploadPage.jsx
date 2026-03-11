import { useState } from 'react';
import DropZone from '../components/upload/DropZone';
import UploadProgress from '../components/upload/UploadProgress';
import { uploadDocument } from '../services/api';

export default function UploadPage() {
  const [files, setFiles] = useState([]);

  const addFiles = (newFiles) => {
    const items = newFiles.map((f) => ({
      file: f,
      name: f.name,
      progress: 0,
      status: 'queue',
    }));
    setFiles((prev) => [...prev, ...items]);
  };

  const processAll = async () => {
    for (let i = 0; i < files.length; i++) {
      if (files[i].status !== 'queue') continue;

      setFiles((prev) =>
        prev.map((f, j) => (j === i ? { ...f, status: 'uploading' } : f))
      );

      try {
        await uploadDocument(files[i].file, (pct) => {
          setFiles((prev) =>
            prev.map((f, j) => (j === i ? { ...f, progress: pct } : f))
          );
        });
        setFiles((prev) =>
          prev.map((f, j) => (j === i ? { ...f, progress: 100, status: 'done' } : f))
        );
      } catch {
        setFiles((prev) =>
          prev.map((f, j) => (j === i ? { ...f, status: 'error' } : f))
        );
      }
    }
  };

  const hasQueued = files.some((f) => f.status === 'queue');

  return (
    <div className="p-4" style={{ backgroundColor: 'var(--bg-primary)', minHeight: '100%' }}>
      <h4 className="mb-1" style={{ color: 'var(--text-primary)' }}>Upload Legal Documents</h4>
      <p className="mb-4" style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        Upload FIRs, court judgments, scanned documents, or audio recordings for processing.
      </p>

      <DropZone onFiles={addFiles} />

      <UploadProgress files={files} />

      {hasQueued && (
        <button
          onClick={processAll}
          className="btn mt-4 px-4 py-2"
          style={{ backgroundColor: 'var(--accent)', color: 'white' }}
        >
          ⚡ Process All Documents
        </button>
      )}
    </div>
  );
}
