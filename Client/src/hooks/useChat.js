import { useState, useCallback } from 'react';
import { queryRAG } from '../services/api';

const WELCOME_MESSAGE = {
  role: 'assistant',
  content:
    'Welcome! Ask me any legal question — FIRs, court judgments, IPC/CrPC/BNS sections, or your uploaded legal documents.',
  verdict: null,
  sources: [],
};

export function useChat() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = useCallback(async (question, docType = null) => {
    if (!question || !question.trim()) return;

    const userMessage = { role: 'user', content: question.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    try {
      const data = await queryRAG(question.trim(), docType);
      const assistantMessage = {
        role: 'assistant',
        content: data.answer || 'No answer generated.',
        verdict: data.verdict,
        reason: data.reason,
        sources: data.sources || [],
        keptStrips: data.kept_strips || [],
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = {
        role: 'assistant',
        content:
          'Sorry, there was an error processing your legal query. Please ensure the backend server is running.',
        verdict: null,
        sources: [],
      };
      setMessages((prev) => [...prev, errorMessage]);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearChat = useCallback(() => {
    setMessages([WELCOME_MESSAGE]);
    setError(null);
  }, []);

  return {
    messages,
    loading,
    error,
    sendMessage,
    clearChat,
  };
}

export default useChat;
