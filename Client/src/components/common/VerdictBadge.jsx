export default function VerdictBadge({ verdict }) {
  const map = {
    CORRECT:   { bg: '#16a34a', icon: '✅', label: 'CORRECT' },
    INCORRECT: { bg: '#dc2626', icon: '❌', label: 'INCORRECT' },
    AMBIGUOUS: { bg: '#d97706', icon: '⚠️', label: 'AMBIGUOUS' },
  };
  const style = map[verdict];
  if (!style) return null;
  return (
    <span
      className="badge rounded-pill px-3 py-2"
      style={{ backgroundColor: style.bg, fontSize: '0.72rem', letterSpacing: '0.05em' }}
    >
      {style.icon} {style.label}
    </span>
  );
}
