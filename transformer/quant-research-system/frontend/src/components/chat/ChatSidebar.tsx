import React, { useState, useMemo } from 'react';
import { COLORS, type ChatSession } from '../../types/chat';

interface ChatSidebarProps {
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onCreateNewChat: () => void;
  onDeleteSession: (sessionId: string) => void;
  isOpen: boolean;
  onToggle: () => void;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onCreateNewChat,
  onDeleteSession,
  isOpen,
  onToggle,
}) => {
  const [hoveredSessionId, setHoveredSessionId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  // Sort sessions by updatedAt (most recent first)
  const sortedSessions = useMemo(() => {
    return [...sessions].sort((a, b) => b.updatedAt - a.updatedAt);
  }, [sessions]);

  const formatDate = (timestamp: number): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    
    if (isToday) {
      return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      });
    }
    
    const isThisYear = date.getFullYear() === now.getFullYear();
    if (isThisYear) {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
    }
    
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: '2-digit'
    });
  };

  const handleDeleteClick = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (confirmDeleteId === sessionId) {
      onDeleteSession(sessionId);
      setConfirmDeleteId(null);
    } else {
      setConfirmDeleteId(sessionId);
      // Auto-clear confirm state after 3 seconds
      setTimeout(() => setConfirmDeleteId(prev => prev === sessionId ? null : prev), 3000);
    }
  };

  return (
    <>
      {/* Sidebar Container */}
      <div
        style={{
          width: isOpen ? 280 : 0,
          minWidth: isOpen ? 280 : 0,
          height: '100%',
          backgroundColor: COLORS.bgPanel,
          borderRight: `1px solid ${COLORS.border}`,
          display: 'flex',
          flexDirection: 'column',
          transition: 'width 0.2s ease, min-width 0.2s ease',
          overflow: 'hidden',
        }}
      >
        {/* Sidebar Header */}
        <div
          style={{
            padding: '12px 16px',
            borderBottom: `1px solid ${COLORS.border}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: COLORS.bgHeader,
          }}
        >
          <span
            style={{
              fontSize: '11px',
              fontWeight: 700,
              color: COLORS.amber,
              textTransform: 'uppercase',
              letterSpacing: '1px',
            }}
          >
            Chat History
          </span>
          <span style={{ fontSize: '10px', color: COLORS.textMuted }}>
            {sessions.length} chat{sessions.length !== 1 ? 's' : ''}
          </span>
        </div>

        {/* New Chat Button */}
        <div style={{ padding: '12px 16px', borderBottom: `1px solid ${COLORS.border}` }}>
          <button
            onClick={onCreateNewChat}
            style={{
              width: '100%',
              padding: '10px 14px',
              backgroundColor: COLORS.amber,
              color: COLORS.bgPrimary,
              border: 'none',
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'opacity 0.15s ease',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.85')}
            onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
          >
            <PlusIcon />
            New Chat
          </button>
        </div>

        {/* Sessions List */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '8px 0',
          }}
        >
          {sortedSessions.length === 0 ? (
            <div
              style={{
                padding: '32px 16px',
                textAlign: 'center',
                color: COLORS.textMuted,
                fontSize: '12px',
              }}
            >
              <p>No chat history yet</p>
              <p style={{ marginTop: '8px', fontSize: '11px' }}>
                Start a new conversation
              </p>
            </div>
          ) : (
            sortedSessions.map((session) => {
              const isActive = session.id === activeSessionId;
              const isHovered = session.id === hoveredSessionId;
              const isConfirmingDelete = confirmDeleteId === session.id;

              return (
                <div
                  key={session.id}
                  onClick={() => onSelectSession(session.id)}
                  onMouseEnter={() => setHoveredSessionId(session.id)}
                  onMouseLeave={() => setHoveredSessionId(null)}
                  style={{
                    padding: '10px 16px',
                    margin: '0 8px 4px 8px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    backgroundColor: isActive
                      ? 'rgba(255, 160, 40, 0.15)'
                      : isHovered
                      ? COLORS.bgHover
                      : 'transparent',
                    borderLeft: isActive ? `3px solid ${COLORS.amber}` : '3px solid transparent',
                    transition: 'background-color 0.15s ease',
                    position: 'relative',
                  }}
                >
                  {/* Session Title */}
                  <div
                    style={{
                      fontSize: '13px',
                      fontWeight: isActive ? 600 : 400,
                      color: isActive ? COLORS.amber : COLORS.textPrimary,
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      marginBottom: '4px',
                      paddingRight: '24px',
                    }}
                  >
                    {session.title}
                  </div>

                  {/* Session Meta */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      fontSize: '10px',
                      color: COLORS.textMuted,
                    }}
                  >
                    <span>{formatDate(session.updatedAt)}</span>
                    <span>{session.messages.length} message{session.messages.length !== 1 ? 's' : ''}</span>
                  </div>

                  {/* Delete Button (appears on hover) */}
                  {(isHovered || isConfirmingDelete) && (
                    <button
                      onClick={(e) => handleDeleteClick(e, session.id)}
                      style={{
                        position: 'absolute',
                        top: '50%',
                        right: '8px',
                        transform: 'translateY(-50%)',
                        width: '20px',
                        height: '20px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        backgroundColor: isConfirmingDelete ? COLORS.red : 'transparent',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: 'pointer',
                        color: isConfirmingDelete ? COLORS.textPrimary : COLORS.textMuted,
                        fontSize: '12px',
                        transition: 'all 0.15s ease',
                      }}
                      title={isConfirmingDelete ? 'Click again to confirm delete' : 'Delete chat'}
                    >
                      {isConfirmingDelete ? '✓' : '×'}
                    </button>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Sidebar Footer */}
        <div
          style={{
            padding: '10px 16px',
            borderTop: `1px solid ${COLORS.border}`,
            fontSize: '10px',
            color: COLORS.textMuted,
            textAlign: 'center',
          }}
        >
          Sessions stored locally
        </div>
      </div>

      {/* Toggle Button (fixed position when sidebar is closed) */}
      <button
        onClick={onToggle}
        style={{
          position: 'fixed',
          left: isOpen ? 280 : 0,
          top: '50%',
          transform: 'translateY(-50%)',
          width: '20px',
          height: '60px',
          backgroundColor: COLORS.bgPanel,
          border: `1px solid ${COLORS.border}`,
          borderLeft: 'none',
          borderRadius: '0 4px 4px 0',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: COLORS.amber,
          fontSize: '12px',
          zIndex: 100,
          transition: 'left 0.2s ease',
        }}
        title={isOpen ? 'Hide sidebar' : 'Show sidebar'}
      >
        {isOpen ? '◀' : '▶'}
      </button>
    </>
  );
};

// Simple Plus Icon Component
const PlusIcon: React.FC = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2.5"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <line x1="12" y1="5" x2="12" y2="19" />
    <line x1="5" y1="12" x2="19" y2="12" />
  </svg>
);

export default ChatSidebar;
