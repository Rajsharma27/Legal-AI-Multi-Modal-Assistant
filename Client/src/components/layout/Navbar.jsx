import { Link, useLocation } from 'react-router-dom';

export default function Navbar() {
  const { pathname } = useLocation();
  const links = [
    { to: '/chat', label: 'Chat' },
    { to: '/upload', label: 'Upload' },
    { to: '/library', label: 'Library' },
  ];

  return (
    <nav
      className="navbar px-4 d-flex align-items-center justify-content-between"
      style={{
        backgroundColor: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border-color)',
        height: '56px',
        flexShrink: 0,
      }}
    >
      <Link className="text-decoration-none fw-bold fs-5" to="/chat" style={{ color: 'var(--text-primary)' }}>
        ⚖️ Legal AI Assistant
      </Link>
      <div className="d-flex gap-2">
        {links.map(({ to, label }) => (
          <Link
            key={to}
            to={to}
            className="btn btn-sm"
            style={{
              backgroundColor: pathname === to ? 'var(--accent)' : 'transparent',
              color: pathname === to ? 'white' : 'var(--text-muted)',
              border: `1px solid ${pathname === to ? 'var(--accent)' : 'var(--border-color)'}`,
            }}
          >
            {label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
