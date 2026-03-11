import { Link } from 'react-router-dom';

const recentQueries = [
  'Bail conditions under IPC 302',
  'CrPC 161 statement admissibility',
  'Cognizable vs non-cognizable offence',
  'FIR registration procedure',
];

const docCounts = [
  { label: 'FIRs', icon: '🚔', count: 0 },
  { label: 'Judgments', icon: '⚖️', count: 0 },
  { label: 'OCR Scans', icon: '🖼️', count: 0 },
  { label: 'Audio', icon: '🎵', count: 0 },
];

export default function Sidebar() {
  return (
    <div
      className="d-flex flex-column p-3"
      style={{
        width: '230px',
        minWidth: '230px',
        backgroundColor: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-color)',
        overflowY: 'auto',
      }}
    >
      <Link
        to="/chat"
        className="btn btn-sm w-100 mb-4"
        style={{ backgroundColor: 'var(--accent)', color: 'white' }}
      >
        + New Chat
      </Link>

      <p className="mb-2" style={{ color: 'var(--text-muted)', fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Recent Queries
      </p>
      <ul className="list-unstyled mb-4">
        {recentQueries.map((q, i) => (
          <li key={i}>
            <Link
              to="/chat"
              className="sidebar-item d-block px-2 py-1 rounded text-decoration-none mb-1"
              style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}
              title={q}
            >
              💬 {q.length > 26 ? q.slice(0, 26) + '…' : q}
            </Link>
          </li>
        ))}
      </ul>

      <p className="mb-2" style={{ color: 'var(--text-muted)', fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Document Types
      </p>
      <ul className="list-unstyled">
        {docCounts.map(({ label, icon, count }) => (
          <li
            key={label}
            className="d-flex justify-content-between align-items-center px-2 py-1 mb-1 rounded"
            style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}
          >
            <span>{icon} {label}</span>
            <span
              className="badge rounded-pill"
              style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-muted)', fontSize: '0.7rem' }}
            >
              {count}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
