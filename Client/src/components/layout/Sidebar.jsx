import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { path: '/chat', label: 'Chat Assistant', icon: '💬' },
  { path: '/upload', label: 'Upload Documents', icon: '📤' },
  { path: '/library', label: 'Document Library', icon: '📂' },
  { path: '/history', label: 'Query History', icon: '📜' },
];

const recentQueries = [
  'Bail conditions under IPC 302',
  'CrPC 161 statement admissibility',
  'Cognizable vs non-cognizable offence',
  'FIR registration procedure',
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <div
      className="d-flex flex-column p-3"
      style={{
        width: '240px',
        minWidth: '240px',
        backgroundColor: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-color)',
        overflowY: 'auto',
      }}
    >
      <Link
        to="/chat"
        className="btn btn-sm w-100 mb-4 fw-semibold"
        style={{ backgroundColor: 'var(--accent)', color: 'white' }}
      >
        + New Legal Chat
      </Link>

      <p className="mb-2" style={{ color: 'var(--text-muted)', fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Navigation
      </p>
      <ul className="list-unstyled mb-4">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <li key={item.path}>
              <Link
                to={item.path}
                className="d-flex align-items-center gap-2 px-3 py-2 rounded text-decoration-none mb-1"
                style={{
                  backgroundColor: isActive ? 'rgba(99,102,241,0.15)' : 'transparent',
                  color: isActive ? 'var(--accent)' : 'var(--text-muted)',
                  fontSize: '0.86rem',
                  fontWeight: isActive ? 600 : 400,
                }}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>

      <p className="mb-2" style={{ color: 'var(--text-muted)', fontSize: '0.68rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Recent Sample Queries
      </p>
      <ul className="list-unstyled">
        {recentQueries.map((q, i) => (
          <li key={i}>
            <Link
              to="/chat"
              className="sidebar-item d-block px-2 py-1 rounded text-decoration-none mb-1"
              style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}
              title={q}
            >
              • {q.length > 24 ? q.slice(0, 24) + '…' : q}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
