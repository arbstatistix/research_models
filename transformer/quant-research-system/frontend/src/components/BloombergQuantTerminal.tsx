import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import 'katex/dist/katex.min.css';
import { ChatSidebar } from './chat/ChatSidebar';
import { useChatHistory } from '../hooks/useChatHistory';
import { COLORS, type ChatMessage, type PipelineResponse } from '../types/chat';

// ============================================================================
// EXTENDED SANITIZE SCHEMA FOR MATH ELEMENTS
// ============================================================================
const sanitizeSchema = {
  ...defaultSchema,
  attributes: {
    ...defaultSchema.attributes,
    span: [...(defaultSchema.attributes?.span || []), 'className'],
    div: [...(defaultSchema.attributes?.div || []), 'className'],
  },
  tagNames: [
    ...(defaultSchema.tagNames || []),
    'math', 'mrow', 'mi', 'mo', 'mn', 'mfrac', 'msqrt', 'msup', 'msub', 'msubsup', 'mtext', 'mspace', 'mstyle',
  ],
};

// ============================================================================
// MARKDOWN PREPROCESSING
// ============================================================================
function preprocessLLMOutput(text: string): string {
  if (!text) return '';

  let cleaned = text;

  // Remove conversation/special tokens
  cleaned = cleaned.replace(/<\|im_start\|>.*?<\|im_end\|>/gs, '');
  cleaned = cleaned.replace(/<\|im_start\|>/g, '');
  cleaned = cleaned.replace(/<\|im_end\|>/g, '');
  cleaned = cleaned.replace(/<\|endoftext\|>/g, '');

  // Remove repeated headers
  cleaned = cleaned.replace(/^(#{1,6}\s*(?:Response|Answer|Output|Result|Final Answer)[:\s]*)+$/gim, '');
  cleaned = cleaned.replace(/^(?:Response|Answer|Output|Result|Final Answer)[:\s]*$/gim, '');

  // Remove excessive rules
  cleaned = cleaned.replace(/(?:^[-*_]{3,}\s*\n){2,}/gm, '---\n');

  // Remove spam patterns
  const spamPatterns = [
    /\[\s*\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[^\]]*\]/g,
    /\{\s*"model"\s*:\s*"[^"]+"\s*,\s*"[^"]+"\s*:\s*[^}]+\}/g,
    /_{10,}/g, /\*{10,}/g, /-{10,}/g, /={10,}/g,
  ];
  spamPatterns.forEach((pattern) => {
    cleaned = cleaned.replace(pattern, '');
  });

  // Deduplicate lines (handles LLM outputting same line with/without LaTeX)
  const lines = cleaned.split('\n');
  const deduped: string[] = [];
  const seen = new Set<string>();

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      deduped.push('');
      continue;
    }

    const normalized = trimmed
      .replace(/\$\$?/g, '')
      .replace(/[_^]\{([^}]+)\}/g, '$1')
      .replace(/[_^](\w)/g, '$1')
      .replace(/\\[a-zA-Z]+/g, '')
      .replace(/\\[\[\]()]/g, '')
      .replace(/[\s\u200B-\u200D\uFEFF]+/g, ' ')
      .replace(/[∗⋆]/g, '*')
      .trim()
      .toLowerCase();

    if (normalized.length > 5 && seen.has(normalized)) {
      continue;
    }

    seen.add(normalized);
    deduped.push(line);
  }
  cleaned = deduped.join('\n');

  // Fix tables
  cleaned = cleaned.replace(/^(\|[-\s]+\|)+$/gm, (match) => {
    return match.replace(/\s+/g, '').replace(/\|/g, ' | ').trim();
  });

  // Clean up blank lines
  cleaned = cleaned.replace(/\n{4,}/g, '\n\n\n');

  return cleaned.trim();
}

// ============================================================================
// MARKDOWN COMPONENTS
// ============================================================================
const markdownComponents: React.ComponentProps<typeof ReactMarkdown>['components'] = {
  table: ({ children }) => (
    <div style={{ overflowX: 'auto', margin: '16px 0' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.95em' }}>
        {children}
      </table>
    </div>
  ),
  thead: ({ children }) => (
    <thead style={{ backgroundColor: COLORS.bgHeader }}>{children}</thead>
  ),
  th: ({ children }) => (
    <th style={{ 
      border: `1px solid ${COLORS.border}`, 
      padding: '10px 12px', 
      textAlign: 'left', 
      color: COLORS.amber,
      fontWeight: 600 
    }}>
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td style={{ 
      border: `1px solid ${COLORS.border}`, 
      padding: '10px 12px',
      color: COLORS.textPrimary
    }}>
      {children}
    </td>
  ),
  tr: ({ children }) => (
    <tr style={{ backgroundColor: 'transparent' }}>{children}</tr>
  ),
  h1: ({ children }) => (
    <h1 style={{ 
      fontSize: '1.4em', 
      color: COLORS.amber, 
      margin: '20px 0 12px 0',
      borderBottom: `1px solid ${COLORS.border}`,
      paddingBottom: '8px',
      fontWeight: 600
    }}>
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 style={{ 
      fontSize: '1.2em', 
      color: COLORS.amber, 
      margin: '16px 0 10px 0',
      fontWeight: 600
    }}>
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 style={{ 
      fontSize: '1.1em', 
      color: COLORS.amber, 
      margin: '14px 0 8px 0',
      fontWeight: 600
    }}>
      {children}
    </h3>
  ),
  h4: ({ children }) => (
    <h4 style={{ 
      fontSize: '1.05em', 
      color: COLORS.amber, 
      margin: '12px 0 6px 0',
      fontWeight: 600
    }}>
      {children}
    </h4>
  ),
  p: ({ children }) => (
    <p style={{ margin: '0 0 12px 0', lineHeight: 1.7, color: COLORS.textPrimary }}>
      {children}
    </p>
  ),
  ul: ({ children }) => (
    <ul style={{ margin: '8px 0 12px 20px', padding: 0, color: COLORS.textPrimary }}>
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol style={{ margin: '8px 0 12px 20px', padding: 0, color: COLORS.textPrimary }}>
      {children}
    </ol>
  ),
  li: ({ children }) => (
    <li style={{ marginBottom: '4px', lineHeight: 1.6 }}>{children}</li>
  ),
  code: ({ inline, children }: { inline?: boolean; className?: string; children?: React.ReactNode }) => {
    if (!inline) {
      return (
        <pre style={{
          backgroundColor: COLORS.bgSecondary,
          padding: '12px 16px',
          borderRadius: '4px',
          overflowX: 'auto',
          fontSize: '0.9em',
          border: `1px solid ${COLORS.border}`,
          margin: '12px 0',
          fontFamily: '"Roboto Mono", "Consolas", monospace',
          color: COLORS.textPrimary
        }}>
          <code style={{ background: 'none', border: 'none', padding: 0 }}>{children}</code>
        </pre>
      );
    }
    return (
      <code style={{
        backgroundColor: COLORS.bgSecondary,
        padding: '2px 6px',
        borderRadius: '3px',
        fontSize: '0.9em',
        border: `1px solid ${COLORS.border}`,
        fontFamily: '"Roboto Mono", "Consolas", monospace',
        color: COLORS.amber
      }}>
        {children}
      </code>
    );
  },
  blockquote: ({ children }) => (
    <blockquote style={{
      borderLeft: `3px solid ${COLORS.amber}`,
      paddingLeft: '16px',
      margin: '12px 0',
      color: COLORS.textSecondary,
      fontStyle: 'italic'
    }}>
      {children}
    </blockquote>
  ),
  hr: () => (
    <hr style={{ border: 'none', borderTop: `1px solid ${COLORS.border}`, margin: '20px 0' }} />
  ),
  a: ({ children, href }: { children?: React.ReactNode; href?: string }) => (
    <a href={href} style={{ color: COLORS.blue, textDecoration: 'underline' }}>
      {children}
    </a>
  ),
  strong: ({ children }) => (
    <strong style={{ color: COLORS.amber, fontWeight: 600 }}>{children}</strong>
  ),
  em: ({ children }) => (
    <em style={{ fontStyle: 'italic' }}>{children}</em>
  ),
};

// ============================================================================
// MESSAGE BUBBLE COMPONENT
// ============================================================================
interface MessageBubbleProps {
  message: ChatMessage;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const processedContent = useMemo(() => {
    if (isUser) return message.content;
    return preprocessLLMOutput(message.content);
  }, [message.content, isUser]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '16px',
      }}
    >
      {/* Role Label */}
      <div
        style={{
          fontSize: '10px',
          color: isUser ? COLORS.amber : COLORS.green,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          marginBottom: '4px',
          fontWeight: 600,
        }}
      >
        {isUser ? 'You' : 'Quant Researcher'}
      </div>

      {/* Message Content */}
      <div
        style={{
          maxWidth: '90%',
          padding: '12px 16px',
          backgroundColor: isUser ? COLORS.bgHeader : COLORS.bgSecondary,
          border: `1px solid ${isUser ? COLORS.borderActive : COLORS.border}`,
          borderRadius: '4px',
          borderTopLeftRadius: isUser ? '4px' : '2px',
          borderTopRightRadius: isUser ? '2px' : '4px',
        }}
      >
        {isUser ? (
          <div style={{ fontSize: '14px', color: COLORS.textPrimary, lineHeight: 1.6 }}>
            {message.content}
          </div>
        ) : (
          <div className="markdown-content">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[[rehypeSanitize, sanitizeSchema], rehypeKatex]}
              components={markdownComponents}
            >
              {processedContent}
            </ReactMarkdown>
          </div>
        )}
      </div>

      {/* Timestamp */}
      <div
        style={{
          fontSize: '10px',
          color: COLORS.textMuted,
          marginTop: '4px',
        }}
      >
        {new Date(message.timestamp).toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
          hour12: true,
        })}
      </div>
    </div>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

function BloombergQuantTerminal() {
  // Chat history hook
  const {
    sessions,
    activeSessionId,
    pendingRequest,
    createNewSession,
    loadSession,
    addMessageToSession,
    deleteSession,
    setActiveSessionId,
    setPendingRequest,
  } = useChatHistory();

  // UI State
  const [command, setCommand] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [progressMessage, setProgressMessage] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date());
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentSessionMessages, setCurrentSessionMessages] = useState<ChatMessage[]>([]);
  const [isRetrying, setIsRetrying] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load active session messages when session changes
  useEffect(() => {
    if (activeSessionId) {
      const session = loadSession(activeSessionId);
      if (session) {
        setCurrentSessionMessages(session.messages);
      }
    } else {
      setCurrentSessionMessages([]);
    }
  }, [activeSessionId, loadSession, sessions]);

  // Handle pending request on page reload
  useEffect(() => {
    if (pendingRequest && !isLoading && !isRetrying) {
      // There's a pending request from before reload
      const session = loadSession(pendingRequest.sessionId);
      if (session) {
        // Check if the assistant already responded (message might have been saved)
        const lastMessage = session.messages[session.messages.length - 1];
        const hasResponse = lastMessage && lastMessage.role === 'assistant' && 
                           lastMessage.timestamp > pendingRequest.timestamp;
        
        if (!hasResponse) {
          // Need to retry the request
          setIsRetrying(true);
          setActiveSessionId(pendingRequest.sessionId);
          retryPendingRequest(pendingRequest);
        } else {
          // Response already exists, clear pending
          setPendingRequest(null);
        }
      } else {
        // Session no longer exists, clear pending
        setPendingRequest(null);
      }
    }
  }, [pendingRequest, isLoading, isRetrying, loadSession, setActiveSessionId, setPendingRequest]);

  // Cleanup abort controller on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSessionMessages, isLoading]);

  // Clock
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Retry a pending request after page reload
  const retryPendingRequest = async (request: typeof pendingRequest) => {
    if (!request) return;
    
    setIsLoading(true);
    setProgressMessage('Reconnecting to backend...');

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('http://localhost:8000/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: request.prompt }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: PipelineResponse = await response.json();

      // Add assistant response
      if (data.success) {
        addMessageToSession(request.sessionId, {
          role: 'assistant',
          content: data.final_answer,
        });
      } else {
        addMessageToSession(request.sessionId, {
          role: 'assistant',
          content: `**Error:** ${data.error || 'Unknown error occurred'}`,
        });
      }
      // Clear pending request on success
      setPendingRequest(null);
    } catch (err) {
      let errorMessage: string;
      if (err instanceof Error) {
        if (err.name === 'AbortError') {
          errorMessage = 'Request was cancelled';
        } else {
          errorMessage = err.message;
        }
      } else {
        errorMessage = 'Network error';
      }
      addMessageToSession(request.sessionId, {
        role: 'assistant',
        content: `**Error:** ${errorMessage}. Please try again.`,
      });
      // Clear pending request even on error
      setPendingRequest(null);
    } finally {
      setIsLoading(false);
      setProgressMessage('');
      setIsRetrying(false);
      abortControllerRef.current = null;
    }
  };

  // Handle creating new chat
  const handleCreateNewChat = useCallback(() => {
    createNewSession();
    setCommand('');
    inputRef.current?.focus();
  }, [createNewSession]);

  // Handle selecting a session
  const handleSelectSession = useCallback((sessionId: string) => {
    setActiveSessionId(sessionId);
    setCommand('');
    inputRef.current?.focus();
  }, [setActiveSessionId]);

  // Submit handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim() || isLoading) return;

    // Ensure we have an active session
    let sessionId = activeSessionId;
    if (!sessionId) {
      sessionId = createNewSession();
    }

    const userMessage = command.trim();
    
    // Add user message immediately
    addMessageToSession(sessionId, {
      role: 'user',
      content: userMessage,
    });

    // Store pending request for recovery on page reload
    const newPendingRequest = {
      sessionId,
      prompt: userMessage,
      timestamp: Date.now(),
      messageId: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    };
    setPendingRequest(newPendingRequest);

    setCommand('');
    setIsLoading(true);
    setProgressMessage('Connecting to backend...');

    // Create AbortController
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('http://localhost:8000/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userMessage }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: PipelineResponse = await response.json();

      // Add assistant response
      if (data.success) {
        addMessageToSession(sessionId, {
          role: 'assistant',
          content: data.final_answer,
        });
      } else {
        addMessageToSession(sessionId, {
          role: 'assistant',
          content: `**Error:** ${data.error || 'Unknown error occurred'}`,
        });
      }
      // Clear pending request on success
      setPendingRequest(null);
    } catch (err) {
      let errorMessage: string;
      let wasAborted = false;
      if (err instanceof Error) {
        if (err.name === 'AbortError') {
          errorMessage = 'Request was cancelled';
          wasAborted = true;
        } else {
          errorMessage = err.message;
        }
      } else {
        errorMessage = 'Network error';
      }
      
      // Only add error message if not aborted (aborted means we're probably reloading)
      if (!wasAborted) {
        addMessageToSession(sessionId, {
          role: 'assistant',
          content: `**Error:** ${errorMessage}. Please ensure the backend is running.`,
        });
        // Clear pending request on error
        setPendingRequest(null);
      }
    } finally {
      setIsLoading(false);
      setProgressMessage('');
      abortControllerRef.current = null;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setCommand('');
    }
  };

  const getStatusText = () => {
    if (isLoading) return 'PROCESSING';
    if (isRetrying) return 'RECONNECTING';
    if (!activeSessionId) return 'IDLE';
    return 'READY';
  };

  const getStatusColor = () => {
    if (isLoading || isRetrying) return COLORS.blue;
    if (!activeSessionId) return COLORS.textMuted;
    return COLORS.green;
  };

  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',
        backgroundColor: COLORS.bgPrimary,
        color: COLORS.textPrimary,
        fontFamily: '"Segoe UI", "Roboto Mono", "Consolas", monospace',
        display: 'flex',
        overflow: 'hidden',
      }}
    >
      {/* Chat History Sidebar */}
      <ChatSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onCreateNewChat={handleCreateNewChat}
        onDeleteSession={deleteSession}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />

      {/* Main Content Area */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          marginLeft: sidebarOpen ? 0 : '20px',
        }}
      >
        {/* TOP COMMAND BAR */}
        <div
          style={{
            backgroundColor: COLORS.bgHeader,
            borderBottom: `2px solid ${COLORS.amber}`,
            padding: '8px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
          }}
        >
          <div
            style={{
              backgroundColor: COLORS.amber,
              color: COLORS.bgPrimary,
              padding: '4px 10px',
              fontWeight: 800,
              fontSize: '12px',
              letterSpacing: '1px',
            }}
          >
            QUANT
          </div>

          <form onSubmit={handleSubmit} style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: COLORS.amber, fontSize: '14px', fontWeight: 600 }}>&gt;</span>
            <input
              ref={inputRef}
              type="text"
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                activeSessionId
                  ? 'Enter research query (e.g., Calculate Black-Scholes Greeks)...'
                  : 'Click "New Chat" to start a conversation...'
              }
              disabled={isLoading || !activeSessionId}
              style={{
                flex: 1,
                backgroundColor: 'transparent',
                border: 'none',
                color: COLORS.textPrimary,
                fontSize: '14px',
                fontFamily: 'inherit',
                outline: 'none',
                padding: '4px 0',
              }}
            />
          </form>

          <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: '11px' }}>
            <span style={{ color: getStatusColor(), fontWeight: 600 }}>
              {(isLoading || isRetrying) && <span style={{ animation: 'pulse 1s infinite' }}>● </span>}
              {getStatusText()}
            </span>
            <span style={{ color: COLORS.textMuted }}>
              {currentTime.toLocaleTimeString('en-US', { hour12: false })}
            </span>
          </div>
        </div>

        {/* MAIN CONTENT */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            padding: 2,
            overflow: 'hidden',
            gap: 2,
          }}
        >
          {/* NO ACTIVE SESSION STATE */}
          {!activeSessionId && (
            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: COLORS.bgPanel,
                border: `1px solid ${COLORS.border}`,
              }}
            >
              <div style={{ textAlign: 'center' }}>
                <p style={{ color: COLORS.amber, fontSize: '14px', fontWeight: 600 }}>
                  QUANTITATIVE RESEARCH PIPELINE
                </p>
                <p style={{ color: COLORS.textMuted, fontSize: '12px', marginTop: 12 }}>
                  Select a chat from the sidebar or create a new one
                </p>
                <button
                  onClick={handleCreateNewChat}
                  style={{
                    marginTop: 20,
                    padding: '10px 20px',
                    backgroundColor: COLORS.amber,
                    color: COLORS.bgPrimary,
                    border: 'none',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Start New Chat
                </button>
              </div>
            </div>
          )}

          {/* EMPTY SESSION STATE */}
          {activeSessionId && currentSessionMessages.length === 0 && !isLoading && !isRetrying && (
            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: COLORS.bgPanel,
                border: `1px solid ${COLORS.border}`,
              }}
            >
              <div style={{ textAlign: 'center' }}>
                <p style={{ color: COLORS.amber, fontSize: '14px', fontWeight: 600 }}>
                  NEW CONVERSATION
                </p>
                <p style={{ color: COLORS.textMuted, fontSize: '12px', marginTop: 12 }}>
                  Enter a query above to begin analysis
                </p>
                <p style={{ color: COLORS.textMuted, fontSize: '11px', marginTop: 20 }}>
                  <span style={{ color: COLORS.amber }}>ESC</span> Clear &nbsp;
                  <span style={{ color: COLORS.amber }}>ENTER</span> Submit
                </p>
              </div>
            </div>
          )}

          {/* RECONNECTING STATE */}
          {isRetrying && (
            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: COLORS.bgPanel,
                border: `1px solid ${COLORS.border}`,
              }}
            >
              <div style={{ textAlign: 'center' }}>
                <div
                  style={{
                    width: 48,
                    height: 48,
                    border: `3px solid ${COLORS.border}`,
                    borderTop: `3px solid ${COLORS.amber}`,
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite',
                    margin: '0 auto',
                  }}
                />
                <p style={{ color: COLORS.amber, marginTop: 20, fontSize: '13px' }}>
                  Reconnecting to backend...
                </p>
                <p style={{ color: COLORS.textMuted, fontSize: '11px', marginTop: 8 }}>
                  Recovering your previous request
                </p>
              </div>
            </div>
          )}

          {/* CHAT MESSAGES */}
          {activeSessionId && currentSessionMessages.length > 0 && !isRetrying && (
            <div
              style={{
                flex: 1,
                backgroundColor: COLORS.bgPanel,
                border: `1px solid ${COLORS.border}`,
                overflow: 'auto',
                padding: '16px',
              }}
            >
              {currentSessionMessages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}

              {/* LOADING STATE */}
              {isLoading && (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-start',
                    marginBottom: '16px',
                  }}
                >
                  <div
                    style={{
                      fontSize: '10px',
                      color: COLORS.green,
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                      marginBottom: '4px',
                      fontWeight: 600,
                    }}
                  >
                    Quant Researcher
                  </div>
                  <div
                    style={{
                      padding: '16px 20px',
                      backgroundColor: COLORS.bgSecondary,
                      border: `1px solid ${COLORS.border}`,
                      borderRadius: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                    }}
                  >
                    <div
                      style={{
                        width: 16,
                        height: 16,
                        border: `2px solid ${COLORS.border}`,
                        borderTop: `2px solid ${COLORS.amber}`,
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite',
                      }}
                    />
                    <span style={{ color: COLORS.amber, fontSize: '13px' }}>{progressMessage}</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* BOTTOM STATUS BAR */}
        <div
          style={{
            backgroundColor: COLORS.bgHeader,
            borderTop: `1px solid ${COLORS.border}`,
            padding: '6px 16px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '10px',
          }}
        >
          <div style={{ color: COLORS.textMuted }}>
            <span style={{ color: COLORS.amber }}>ESC</span> CLEAR &nbsp;
            <span style={{ color: COLORS.amber }}>ENTER</span> SUBMIT &nbsp;
            <span style={{ color: COLORS.amber }}>▶/◀</span> TOGGLE SIDEBAR
          </div>
          <div style={{ display: 'flex', gap: 16, color: COLORS.textSecondary }}>
            <span>Quant Research Pipeline v1.0</span>
            <span style={{ color: COLORS.green }}>● CONNECTED</span>
          </div>
        </div>
      </div>

      {/* GLOBAL STYLES */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        ::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }
        ::-webkit-scrollbar-track {
          background: ${COLORS.bgSecondary};
        }
        ::-webkit-scrollbar-thumb {
          background: ${COLORS.border};
          border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
          background: ${COLORS.textMuted};
        }
        ::selection {
          background-color: rgba(255, 160, 40, 0.3);
          color: #ffffff;
        }
        /* KaTeX overrides for dark theme */
        .markdown-content .katex {
          font-size: 1.05em;
          color: ${COLORS.textPrimary};
        }
        .markdown-content .katex-display {
          margin: 16px 0;
          overflow-x: auto;
        }
      `}</style>
    </div>
  );
}

export default BloombergQuantTerminal;
