export default function SourceCard({ source, docType }) {
  const icons = {
    fir: '🚔',
    judgment: '⚖️',
    image_ocr: '🖼️',
    audio_transcript: '🎵',
    document: '📄',
    web: '🌐',
  };
  const icon = icons[docType] || '📄';
  const name = source?.split('/').pop() || source || 'unknown';

  return (
    <span
      className="d-inline-flex align-items-center gap-1 me-2 mb-1 px-2 py-1 rounded"
      style={{
        backgroundColor: 'var(--bg-primary)',
        border: '1px solid var(--border-color)',
        color: 'var(--text-muted)',
        fontSize: '0.76rem',
        maxWidth: '220px',
      }}
    >
      <span>{icon}</span>
      <span className="text-truncate" style={{ maxWidth: '130px' }} title={name}>{name}</span>
      <span
        className="badge rounded-pill ms-1"
        style={{ backgroundColor: 'rgba(99,102,241,0.15)', color: 'var(--accent)', fontSize: '0.65rem' }}
      >
        {docType}
      </span>
    </span>
  );
}
