import { useState, useEffect } from 'react';
import Spinner from '../components/common/Spinner';
import VerdictBadge from '../components/common/VerdictBadge';

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    // Simulated or fetched query history logs
    const fetchHistory = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/health');
        if (res.ok) {
          // Connected to server
        }
      } catch (e) {
        console.warn('Backend server not connected');
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const mockLogs = [
    {
      id: 1,
      question: 'What are the conditions for granting bail under Section 437 CrPC?',
      verdict: 'CORRECT',
      reason: 'Matched Section 437 CrPC statutory criteria.',
      answer: 'Bail under Section 437 CrPC is granted at the discretion of the court for non-bailable offences subject to conditions including non-tampering of evidence.',
      created_at: '2026-09-01T08:30:00Z',
    },
    {
      id: 2,
      question: 'Admissibility of electronic records under Section 65B of Evidence Act',
      verdict: 'CORRECT',
      reason: 'Matched Arjun Panditrao Khotkar judgment precedent.',
      answer: 'A certificate under Section 65B(4) is mandatory for producing electronic evidence as held in Arjun Panditrao Khotkar v. Kailash Kushanrao Gorantyal.',
      created_at: '2026-08-31T14:15:00Z',
    },
    {
      id: 3,
      question: 'Recent Supreme Court ruling on anticipatory bail limitation',
      verdict: 'AMBIGUOUS',
      reason: 'Web search fallback was required for recent case citations.',
      answer: 'Anticipatory bail is generally not limited by time unless exceptional circumstances exist, as reaffirmed in Sushila Aggarwal v. State (NCT of Delhi).',
      created_at: '2026-08-30T11:20:00Z',
    },
  ];

  const displayLogs = history.length > 0 ? history : mockLogs;
  const filtered = displayLogs.filter((item) =>
    item.question.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-4" style={{ backgroundColor: 'var(--bg-primary)', minHeight: '100%' }}>
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
        <div>
          <h4 className="mb-0" style={{ color: 'var(--text-primary)' }}>Query History & Audit Logs</h4>
          <small style={{ color: 'var(--text-muted)' }}>{filtered.length} queries logged</small>
        </div>
        <input
          type="text"
          placeholder="🔍  Search query history..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="form-control form-control-sm"
          style={{
            width: '260px',
            backgroundColor: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-color)',
          }}
        />
      </div>

      {loading ? (
        <div className="d-flex justify-content-center mt-5">
          <Spinner />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-5" style={{ color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '3rem', marginBottom: 12 }}>📜</div>
          <p>No queries found in history.</p>
        </div>
      ) : (
        <div className="d-flex flex-column gap-3">
          {filtered.map((item) => (
            <div
              key={item.id}
              className="p-3 rounded-3"
              style={{
                backgroundColor: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
              }}
            >
              <div className="d-flex justify-content-between align-items-start mb-2 flex-wrap gap-2">
                <div className="fw-semibold" style={{ color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                  💬 {item.question}
                </div>
                <div className="d-flex align-items-center gap-2">
                  <VerdictBadge verdict={item.verdict} />
                  <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                    {new Date(item.created_at).toLocaleDateString('en-IN', {
                      day: '2-digit',
                      month: 'short',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </small>
                </div>
              </div>

              <p className="mb-0" style={{ color: 'var(--text-muted)', fontSize: '0.86rem', lineHeight: 1.6 }}>
                {item.answer}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
