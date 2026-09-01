import { useRef, useEffect } from 'react';
import ChatInput from '../components/chat/ChatInput';
import MessageBubble from '../components/chat/MessageBubble';
import Spinner from '../components/common/Spinner';
import { useChat } from '../hooks/useChat';

export default function ChatPage() {
  const { messages, loading, sendMessage, clearChat } = useChat();
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div className="d-flex flex-column" style={{ height: '100%' }}>
      {/* Top Header bar with clear button */}
      <div
        className="px-4 py-2 d-flex justify-content-between align-items-center"
        style={{
          backgroundColor: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border-color)',
        }}
      >
        <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
          ⚖️ <span className="fw-semibold" style={{ color: 'var(--text-primary)' }}>Indian Legal Intelligence AI</span> — Self-Corrective RAG (Self-RAG) Active
        </div>
        {messages.length > 1 && (
          <button
            onClick={clearChat}
            className="btn btn-sm text-muted"
            style={{ fontSize: '0.78rem' }}
          >
            Clear Chat
          </button>
        )}
      </div>

      {/* Message list area */}
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
                Analyzing legal precedents & statutory context…
              </span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <ChatInput onSend={sendMessage} disabled={loading} />
    </div>
  );
}
