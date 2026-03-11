import { useState, useRef, useEffect } from 'react';
import ChatInput from '../components/chat/ChatInput';
import MessageBubble from '../components/chat/MessageBubble';
import Spinner from '../components/common/Spinner';
import { queryRAG } from '../services/api';

const WELCOME = {
  role: 'assistant',
  content:
    'Welcome! Ask me any question about Indian law — FIRs, court judgments, IPC/CrPC sections, or your uploaded case documents.',
  verdict: null,
  sources: [],
};

export default function ChatPage() {
  const [messages, setMessages] = useState([WELCOME]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (question, docType) => {
    setMessages((prev) => [...prev, { role: 'user', content: question }]);
    setLoading(true);
    try {
      const data = await queryRAG(question, docType);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          verdict: data.verdict,
          reason: data.reason,
          sources: data.sources,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, there was an error processing your query. Please check that the server is running.',
          verdict: null,
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="d-flex flex-column" style={{ height: '100%' }}>
      {/* Message area */}
      <div
        className="flex-grow-1 overflow-auto p-4"
        style={{ backgroundColor: 'var(--bg-primary)' }}
      >
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {loading && (
          <div className="d-flex mb-4 align-items-start gap-2">
            <div
              className="rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
              style={{ width: 36, height: 36, backgroundColor: '#334155', fontSize: '1rem' }}
            >
              ⚖️
            </div>
            <div
              className="px-4 py-3 rounded-3 d-flex align-items-center gap-2"
              style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)' }}
            >
              <Spinner size="sm" />
              <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                Searching legal documents…
              </span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  );
}
