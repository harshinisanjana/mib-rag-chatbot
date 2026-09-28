import { useState, useRef, useEffect, useCallback } from 'react';
import { marked } from 'marked';
import { sendMessage } from './api';
import './App.css';

const SUGGESTIONS = [
  'What services does MIB Tech Solutions provide?',
  'Do you offer free consultations?',
  'What is your support and SLA process?',
];

function TypingIndicator() {
  return (
    <div className="message-row">
      <div className="author-avatar">
        <img src="/mib-logo.png" alt="MIB Assistant" className="author-avatar-img" />
      </div>
      <div className="message-body">
        <span className="author-name">MIB Assistant</span>
        <div className="message-bubble typing-indicator" aria-label="Generating response">
          <span className="dot" /><span className="dot" /><span className="dot" />
        </div>
      </div>
    </div>
  );
}

function SourceChips({ sources }) {
  if (!sources || sources.length === 0) return null;
  return (
    <details className="sources-expander">
      <summary className="sources-header">
        <svg viewBox="0 0 20 20" fill="currentColor" width="13" height="13">
          <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
        </svg>
        <span>Sources &middot; {sources.length}</span>
      </summary>
      <div className="sources-chips">
        {sources.map((s, i) => (
          <span
            key={i}
            className="source-chip"
            title={`Relevance: ${(s.similarity_score * 100).toFixed(0)}%`}
          >
            {s.document_name}
            {s.page != null && ` · p${s.page}`}
            {` · §${s.chunk_index + 1}`}
          </span>
        ))}
      </div>
    </details>
  );
}

function ChatMessage({ msg }) {
  const isUser = msg.role === 'user';
  const html = { __html: marked.parse(msg.content, { async: false }) };

  return (
    <article className={`message-row ${isUser ? 'is-user' : ''}`}>
      {!isUser && (
        <div className="author-avatar">
          <img src="/mib-logo.png" alt="MIB Assistant" className="author-avatar-img" />
        </div>
      )}
      <div className="message-body">
        <span className="author-name">{isUser ? 'You' : 'MIB Assistant'}</span>
        <div className={`message-bubble ${isUser ? 'bubble-user' : ''}`}>
          <div className="bubble-text" dangerouslySetInnerHTML={html} />
          {!isUser && <SourceChips sources={msg.sources} />}
        </div>
      </div>
      {isUser && (
        <div className="author-avatar user-avatar">
          <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
            <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
          </svg>
        </div>
      )}
    </article>
  );
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m the MIB Knowledge Assistant. Ask me anything about MIB Tech Solutions — services, products, support, or documentation.',
      grounded: true,
    },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      setTimeout(() => {
        scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
      }, 50);
    }
  }, []);

  useEffect(scrollToBottom, [messages, sending, scrollToBottom]);

  const handleSend = useCallback(async (text) => {
    const value = (text || input).trim();
    if (!value || sending) return;

    setMessages(prev => [...prev, { role: 'user', content: value }]);
    setInput('');
    setError('');
    setSending(true);

    try {
      const response = await sendMessage(value, sessionId);
      setSessionId(response.session_id);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: response.answer,
          grounded: response.grounded,
          sources: response.sources,
        },
      ]);
    } catch (err) {
      setError(err.message || 'The service is temporarily unavailable. Please try again.');
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  }, [input, sending, sessionId]);

  const handleSubmit = (e) => {
    e.preventDefault();
    handleSend();
  };

  const showWelcome = messages.length === 1 && !sending;

  return (
    <main className="chat-page">
      <section className="chat-shell">
        {/* Header */}
        <header className="chat-header">
          <div className="chat-header-identity">
            <div className="header-avatar-wrap">
              <img src="/mib-logo.png" alt="MIB Tech Solutions" className="header-avatar-img" />
              <span className="status-indicator" title="Online" />
            </div>
            <div className="header-details">
              <h1>MIB Assistant</h1>
              <p className="status-text">
                <span className="status-dot" />
                Powered by Llama 3.2 &middot; RAG Pipeline
              </p>
            </div>
          </div>
        </header>

        {/* Messages */}
        <div className="conversation-container" ref={scrollRef} role="log" aria-live="polite">
          {showWelcome ? (
            <div className="welcome-screen">
              <div className="welcome-badge">
                <img src="/mib-logo.png" alt="MIB Tech Solutions" className="welcome-logo" />
              </div>
              <h2>How can I help?</h2>
              <p className="welcome-desc">
                Ask me anything about MIB Tech Solutions — services, products, support processes, or technical documentation.
              </p>
              <div className="suggestions-panel">
                <span className="suggestions-label">Suggested questions</span>
                <div className="suggestions-grid">
                  {SUGGESTIONS.map(s => (
                    <button key={s} type="button" className="suggestion-pill" onClick={() => handleSend(s)}>
                      <span>{s}</span>
                      <svg viewBox="0 0 20 20" fill="currentColor" width="14" height="14">
                        <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                      </svg>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="message-feed">
              {messages.map((msg, i) => <ChatMessage key={i} msg={msg} />)}
              {sending && <TypingIndicator />}
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="error-banner" role="alert">
            <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {/* Input */}
        <footer className="composer-container">
          <form className="composer-form" onSubmit={handleSubmit}>
            <label className="sr-only" htmlFor="chat-input">Type your message</label>
            <input
              ref={inputRef}
              id="chat-input"
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask a question about MIB Tech Solutions..."
              autoComplete="off"
              disabled={sending}
            />
            <button type="submit" className="send-btn" disabled={sending || !input.trim()}>
              <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
              </svg>
            </button>
          </form>
          <p className="composer-disclaimer">
            Answers are grounded in MIB verified documentation via RAG pipeline.
          </p>
        </footer>
      </section>
    </main>
  );
}
