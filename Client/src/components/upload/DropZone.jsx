import { useState, useRef } from 'react';

const ACCEPTED = '.pdf,.png,.jpg,.jpeg,.tiff,.tif,.bmp,.webp,.mp3,.wav,.m4a';

export default function DropZone({ onFiles }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handle = (files) => {
    const arr = Array.from(files);
    if (arr.length) onFiles(arr);
  };

  return (
    <div
      className="rounded-3 d-flex flex-column align-items-center justify-content-center p-5 text-center"
      onClick={() => inputRef.current.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); handle(e.dataTransfer.files); }}
      style={{
        border: `2px dashed ${dragging ? 'var(--accent)' : 'var(--border-color)'}`,
        backgroundColor: dragging ? 'rgba(99,102,241,0.07)' : 'var(--bg-secondary)',
        cursor: 'pointer',
        transition: 'border-color 0.2s, background-color 0.2s',
        minHeight: '220px',
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        multiple
        hidden
        onChange={(e) => handle(e.target.files)}
      />
      <div style={{ fontSize: '3rem', lineHeight: 1 }}>☁️</div>
      <h5 className="mt-3 mb-1" style={{ color: 'var(--text-primary)' }}>
        Drag &amp; Drop files here
      </h5>
      <p className="mb-3" style={{ color: 'var(--text-muted)' }}>or click to browse</p>
      <small style={{ color: 'var(--text-muted)' }}>
        Supports: PDF · PNG · JPG · TIFF · MP3 · WAV
      </small>
    </div>
  );
}
