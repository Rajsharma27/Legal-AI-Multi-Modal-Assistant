function fileIcon(name) {
  if (/\.pdf$/i.test(name)) return '📄';
  if (/\.(png|jpg|jpeg|tiff|tif|bmp|webp)$/i.test(name)) return '🖼️';
  if (/\.(mp3|wav|m4a)$/i.test(name)) return '🎵';
  return '📎';
}

const STATUS_COLOR = {
  done: '#16a34a',
  error: '#dc2626',
  uploading: 'var(--accent)',
  queue: 'var(--border-color)',
};

export default function UploadProgress({ files }) {
  if (!files.length) return null;

  return (
    <div className="mt-4">
      <p
        className="mb-2"
        style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}
      >
        Uploaded Files
      </p>
      <div
        className="rounded-3 p-3"
        style={{ backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}
      >
        {files.map((f, i) => (
          <div key={i} className="mb-3">
            <div className="d-flex justify-content-between align-items-center mb-1">
              <span style={{ color: 'var(--text-primary)', fontSize: '0.88rem' }}>
                {fileIcon(f.name)} {f.name}
              </span>
              <span style={{ color: STATUS_COLOR[f.status], fontSize: '0.82rem', flexShrink: 0, marginLeft: 8 }}>
                {f.status === 'done'
                  ? '✓ Done'
                  : f.status === 'error'
                  ? '✗ Error'
                  : f.status === 'queue'
                  ? 'Queued'
                  : `${f.progress}%`}
              </span>
            </div>
            <div className="progress" style={{ height: '4px', backgroundColor: 'var(--bg-primary)' }}>
              <div
                className="progress-bar"
                style={{
                  width: `${f.progress}%`,
                  backgroundColor: STATUS_COLOR[f.status],
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
