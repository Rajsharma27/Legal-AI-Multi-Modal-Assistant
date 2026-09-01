import DropZone from '../components/upload/DropZone';
import UploadProgress from '../components/upload/UploadProgress';
import { useUpload } from '../hooks/useUpload';

export default function UploadPage() {
  const { files, isProcessing, addFiles, processAll } = useUpload();
  const hasQueued = files.some((f) => f.status === 'queue');

  return (
    <div className="p-4" style={{ backgroundColor: 'var(--bg-primary)', minHeight: '100%' }}>
      <h4 className="mb-1" style={{ color: 'var(--text-primary)' }}>Upload Legal Documents</h4>
      <p className="mb-4" style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        Upload FIRs, court judgments, scanned images (OCR), or audio recordings (Whisper transcription) for automatic embedding.
      </p>

      <DropZone onFiles={addFiles} />

      <UploadProgress files={files} />

      {hasQueued && (
        <button
          onClick={processAll}
          disabled={isProcessing}
          className="btn mt-4 px-4 py-2 fw-semibold"
          style={{ backgroundColor: 'var(--accent)', color: 'white' }}
        >
          {isProcessing ? '⚡ Processing Documents...' : '⚡ Process All Documents'}
        </button>
      )}
    </div>
  );
}
