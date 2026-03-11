import VerdictBadge from '../common/VerdictBadge';
import SourceCard from './SourceCard';

export default function MessageBubble({ message }) {
  const { role, content, verdict, reason, sources } = message;
  const isUser = role === 'user';

  if (isUser) {
    return (
      <div className="d-flex justify-content-end mb-4 align-items-end gap-2">
        <div
          className="px-4 py-3 rounded-3"
          style={{
            maxWidth: '68%',
            backgroundColor: 'var(--accent)',
            color: 'white',
            lineHeight: 1.6,
          }}
        >
          {content}
        </div>
        <div
          className="rounded-circle d-flex align-items-center justify-content-center fw-bold flex-shrink-0"
          style={{ width: 36, height: 36, backgroundColor: 'var(--accent-hover)', color: 'white', fontSize: '0.8rem' }}
        >
          U
        </div>
      </div>
    );
  }

  return (
    <div className="d-flex mb-4 align-items-start gap-2">
      <div
        className="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0 mt-1"
        style={{ width: 36, height: 36, backgroundColor: '#334155', fontSize: '1rem' }}
      >
        ⚖️
      </div>
      <div
        className="px-4 py-3 rounded-3 flex-grow-1"
        style={{
          maxWidth: '80%',
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
        }}
      >
        <p className="mb-3" style={{ color: 'var(--text-primary)', lineHeight: 1.75, whiteSpace: 'pre-wrap' }}>
          {content}
        </p>

        {verdict && (
          <div className="d-flex align-items-center gap-2 mb-3 flex-wrap">
            <VerdictBadge verdict={verdict} />
            {reason && (
              <small style={{ color: 'var(--text-muted)', fontSize: '0.78rem' }}>{reason}</small>
            )}
          </div>
        )}

        {sources?.length > 0 && (
          <div>
            <p
              className="mb-2"
              style={{ color: 'var(--text-muted)', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}
            >
              Sources
            </p>
            <div className="d-flex flex-wrap">
              {sources.map((s, i) => (
                <SourceCard key={i} source={s.source} docType={s.doc_type} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
