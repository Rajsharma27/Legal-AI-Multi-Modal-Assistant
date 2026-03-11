import { useState } from 'react';

const DOC_TYPES = [
  { value: '', label: 'All Documents' },
  { value: 'fir', label: '🚔 FIR' },
  { value: 'judgment', label: '⚖️ Judgment' },
  { value: 'image_ocr', label: '🖼️ OCR Scan' },
  { value: 'audio_transcript', label: '🎵 Audio' },
];

export default function ChatInput({ onSend, disabled }) {
  const [question, setQuestion] = useState('');
  const [docType, setDocType] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!question.trim() || disabled) return;
    onSend(question.trim(), docType || null);
    setQuestion('');
  };

  return (
    <div
      className="p-3"
      style={{
        backgroundColor: 'var(--bg-secondary)',
        borderTop: '1px solid var(--border-color)',
        flexShrink: 0,
      }}
    >
      <form onSubmit={handleSubmit} className="d-flex gap-2 align-items-end">
        <select
          value={docType}
          onChange={(e) => setDocType(e.target.value)}
          className="form-select form-select-sm"
          style={{
            width: '148px',
            flexShrink: 0,
            backgroundColor: 'var(--bg-primary)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-color)',
          }}
        >
          {DOC_TYPES.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>

        <textarea
          className="form-control"
          rows={1}
          placeholder="Type your legal question… (Shift+Enter for new line)"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          disabled={disabled}
          style={{
            resize: 'none',
            backgroundColor: 'var(--bg-primary)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border-color)',
            lineHeight: 1.5,
          }}
        />

        <button
          type="submit"
          disabled={!question.trim() || disabled}
          className="btn px-3 flex-shrink-0"
          style={{
            backgroundColor: 'var(--accent)',
            color: 'white',
            opacity: !question.trim() || disabled ? 0.5 : 1,
          }}
        >
          ➤
        </button>
      </form>
    </div>
  );
}
