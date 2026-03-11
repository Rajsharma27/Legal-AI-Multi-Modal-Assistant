export default function Spinner({ size = 'sm' }) {
  return (
    <div
      className={`spinner-border spinner-border-${size}`}
      role="status"
      style={{ color: 'var(--accent)' }}
    >
      <span className="visually-hidden">Loading...</span>
    </div>
  );
}
