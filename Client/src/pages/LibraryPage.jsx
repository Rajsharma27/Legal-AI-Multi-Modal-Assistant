import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Spinner from '../components/common/Spinner';
import { fetchDocuments, deleteDocument } from '../services/api';

const DOC_FILTERS = ['All', 'fir', 'judgment', 'image_ocr', 'audio_transcript'];

const ICON = {
  fir: '🚔',
  judgment: '⚖️',
  image_ocr: '🖼️',
  audio_transcript: '🎵',
  document: '📄',
};

export default function LibraryPage() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('All');
  const [search, setSearch] = useState('');
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    fetchDocuments()
      .then(setDocs)
      .catch(() => setDocs([]))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this document and its vector embeddings?')) {
      return;
    }
    setDeletingId(docId);
    try {
      await deleteDocument(docId);
      setDocs((prev) => prev.filter((d) => d.id !== docId));
    } catch (err) {
      alert('Failed to delete document: ' + err.message);
    } finally {
      setDeletingId(null);
    }
  };

  const filtered = docs.filter(
    (d) =>
      (filter === 'All' || d.doc_type === filter) &&
      (d.file_name || d.file_path || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-4" style={{ backgroundColor: 'var(--bg-primary)', minHeight: '100%' }}>
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
        <div>
          <h4 className="mb-0" style={{ color: 'var(--text-primary)' }}>Document Library</h4>
          <small style={{ color: 'var(--text-muted)' }}>{docs.length} documents indexed</small>
        </div>
        <input
          type="text"
          placeholder="🔍  Search documents..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="form-control form-control-sm"
          style={{
            width: '240px',
            backgroundColor: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-color)',
          }}
        />
      </div>

      {/* Filter tabs */}
      <div className="d-flex gap-2 mb-4 flex-wrap">
        {DOC_FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className="btn btn-sm"
            style={{
              backgroundColor: filter === f ? 'var(--accent)' : 'var(--bg-secondary)',
              color: filter === f ? 'white' : 'var(--text-muted)',
              border: '1px solid var(--border-color)',
              textTransform: 'capitalize',
            }}
          >
            {f === 'All' ? 'All' : f.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="d-flex justify-content-center mt-5">
          <Spinner />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-5" style={{ color: 'var(--text-muted)' }}>
          <div style={{ fontSize: '3rem', marginBottom: 12 }}>📂</div>
          <p className="mb-1">No documents found.</p>
          <Link to="/upload" style={{ color: 'var(--accent)' }}>
            Upload some documents
          </Link>
        </div>
      ) : (
        <div className="row g-3">
          {filtered.map((doc) => (
            <div key={doc.id || doc.file_path} className="col-sm-6 col-md-4 col-lg-3">
              <div
                className="rounded-3 p-3 h-100 d-flex flex-column"
                style={{
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  transition: 'border-color 0.2s',
                }}
              >
                <div style={{ fontSize: '2.2rem', marginBottom: 8 }}>
                  {ICON[doc.doc_type] || '📄'}
                </div>

                <div
                  className="fw-semibold mb-1 text-truncate"
                  style={{ color: 'var(--text-primary)', fontSize: '0.88rem' }}
                  title={doc.file_name || doc.file_path}
                >
                  {doc.file_name || (doc.file_path || '').split('/').pop() || 'Unnamed'}
                </div>

                <div className="mb-2 d-flex align-items-center gap-2">
                  <span
                    className="badge rounded-pill px-2 py-1"
                    style={{
                      backgroundColor: 'rgba(99,102,241,0.18)',
                      color: 'var(--accent)',
                      fontSize: '0.7rem',
                      textTransform: 'capitalize',
                    }}
                  >
                    {(doc.doc_type || 'document').replace(/_/g, ' ')}
                  </span>
                  {doc.chunk_count > 0 && (
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      {doc.chunk_count} chunks
                    </span>
                  )}
                </div>

                <small style={{ color: 'var(--text-muted)' }}>
                  {doc.created_at
                    ? new Date(doc.created_at).toLocaleDateString('en-IN', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                      })
                    : '—'}
                </small>

                <div className="mt-auto pt-3 d-flex gap-2">
                  <button
                    onClick={() => handleDelete(doc.id)}
                    disabled={deletingId === doc.id}
                    className="btn btn-sm w-100"
                    style={{
                      backgroundColor: 'rgba(220,38,38,0.1)',
                      color: '#dc2626',
                      border: '1px solid rgba(220,38,38,0.25)',
                      fontSize: '0.78rem',
                    }}
                  >
                    {deletingId === doc.id ? 'Deleting...' : '🗑 Delete'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
