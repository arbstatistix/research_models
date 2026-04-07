import { useState, useEffect, useCallback, useRef } from 'react';
import type { ChatSession, ChatMessage } from '../types/chat';

const STORAGE_KEY = 'quant-research-chat-sessions';
const ACTIVE_SESSION_KEY = 'quant-research-active-session';
const PENDING_REQUEST_KEY = 'quant-research-pending-request';
const MAX_SESSIONS = 100;

export interface PendingRequest {
  sessionId: string;
  prompt: string;
  timestamp: number;
  messageId: string;
}

export interface UseChatHistoryReturn {
  sessions: ChatSession[];
  activeSessionId: string | null;
  pendingRequest: PendingRequest | null;
  createNewSession: () => string;
  loadSession: (sessionId: string) => ChatSession | null;
  addMessageToSession: (sessionId: string, message: Omit<ChatMessage, 'id' | 'timestamp'>) => string;
  updateSessionTitle: (sessionId: string, title: string) => void;
  deleteSession: (sessionId: string) => void;
  clearAllSessions: () => void;
  setActiveSessionId: (id: string | null) => void;
  setPendingRequest: (request: PendingRequest | null) => void;
  updateMessageInSession: (sessionId: string, messageId: string, updates: Partial<ChatMessage>) => void;
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

function generateTitleFromMessage(content: string): string {
  const clean = content.trim().replace(/\s+/g, ' ');
  if (clean.length <= 40) return clean;
  return clean.substring(0, 40) + '...';
}

export function useChatHistory(): UseChatHistoryReturn {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionIdState] = useState<string | null>(null);
  const [pendingRequest, setPendingRequestState] = useState<PendingRequest | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const isUpdatingRef = useRef(false);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          setSessions(parsed);
        }
      }
      const activeStored = localStorage.getItem(ACTIVE_SESSION_KEY);
      if (activeStored) {
        setActiveSessionIdState(activeStored);
      }
      const pendingStored = localStorage.getItem(PENDING_REQUEST_KEY);
      if (pendingStored) {
        setPendingRequestState(JSON.parse(pendingStored));
      }
    } catch (error) {
      console.error('Failed to load chat sessions:', error);
    }
    setIsLoaded(true);
  }, []);

  // Save sessions to localStorage
  useEffect(() => {
    if (isLoaded && !isUpdatingRef.current) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
      } catch (error) {
        console.error('Failed to save chat sessions:', error);
        if (error instanceof Error && error.name === 'QuotaExceededError') {
          const trimmed = sessions.slice(-50);
          setSessions(trimmed);
          try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
          } catch (e) {
            console.error('Still failed after trimming:', e);
          }
        }
      }
    }
  }, [sessions, isLoaded]);

  // Save active session to localStorage
  useEffect(() => {
    if (isLoaded) {
      if (activeSessionId) {
        localStorage.setItem(ACTIVE_SESSION_KEY, activeSessionId);
      } else {
        localStorage.removeItem(ACTIVE_SESSION_KEY);
      }
    }
  }, [activeSessionId, isLoaded]);

  // Save pending request to localStorage
  useEffect(() => {
    if (isLoaded) {
      if (pendingRequest) {
        localStorage.setItem(PENDING_REQUEST_KEY, JSON.stringify(pendingRequest));
      } else {
        localStorage.removeItem(PENDING_REQUEST_KEY);
      }
    }
  }, [pendingRequest, isLoaded]);

  const setActiveSessionId = useCallback((id: string | null) => {
    setActiveSessionIdState(id);
  }, []);

  const setPendingRequest = useCallback((request: PendingRequest | null) => {
    setPendingRequestState(request);
  }, []);

  const createNewSession = useCallback((): string => {
    const now = Date.now();
    const newSession: ChatSession = {
      id: generateId(),
      title: 'New Chat',
      messages: [],
      createdAt: now,
      updatedAt: now,
    };
    
    setSessions(prev => {
      const updated = [newSession, ...prev].slice(0, MAX_SESSIONS);
      return updated;
    });
    
    setActiveSessionIdState(newSession.id);
    return newSession.id;
  }, []);

  const loadSession = useCallback((sessionId: string): ChatSession | null => {
    return sessions.find(s => s.id === sessionId) || null;
  }, [sessions]);

  const addMessageToSession = useCallback((
    sessionId: string, 
    message: Omit<ChatMessage, 'id' | 'timestamp'>
  ): string => {
    const now = Date.now();
    const messageId = generateId();
    const newMessage: ChatMessage = {
      ...message,
      id: messageId,
      timestamp: now,
    };

    isUpdatingRef.current = true;
    setSessions(prev => {
      const updated = prev.map(session => {
        if (session.id !== sessionId) return session;

        const updatedMessages = [...session.messages, newMessage];
        
        let updatedTitle = session.title;
        if (session.title === 'New Chat' && message.role === 'user') {
          updatedTitle = generateTitleFromMessage(message.content);
        }

        return {
          ...session,
          title: updatedTitle,
          messages: updatedMessages,
          updatedAt: now,
        };
      });
      
      // Save immediately for this update
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {
        console.error('Failed to save after adding message:', e);
      }
      
      return updated;
    });
    isUpdatingRef.current = false;
    
    return messageId;
  }, []);

  const updateMessageInSession = useCallback((
    sessionId: string,
    messageId: string,
    updates: Partial<ChatMessage>
  ) => {
    isUpdatingRef.current = true;
    setSessions(prev => {
      const updated = prev.map(session => {
        if (session.id !== sessionId) return session;

        return {
          ...session,
          messages: session.messages.map(msg =>
            msg.id === messageId ? { ...msg, ...updates } : msg
          ),
          updatedAt: Date.now(),
        };
      });
      
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {
        console.error('Failed to save after updating message:', e);
      }
      
      return updated;
    });
    isUpdatingRef.current = false;
  }, []);

  const updateSessionTitle = useCallback((sessionId: string, title: string) => {
    setSessions(prev => prev.map(session => 
      session.id === sessionId 
        ? { ...session, title: title.trim(), updatedAt: Date.now() }
        : session
    ));
  }, []);

  const deleteSession = useCallback((sessionId: string) => {
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    if (activeSessionId === sessionId) {
      setActiveSessionIdState(null);
    }
    // Also clear pending request if it was for this session
    if (pendingRequest?.sessionId === sessionId) {
      setPendingRequestState(null);
    }
  }, [activeSessionId, pendingRequest]);

  const clearAllSessions = useCallback(() => {
    setSessions([]);
    setActiveSessionIdState(null);
    setPendingRequestState(null);
  }, []);

  return {
    sessions,
    activeSessionId,
    pendingRequest,
    createNewSession,
    loadSession,
    addMessageToSession,
    updateSessionTitle,
    deleteSession,
    clearAllSessions,
    setActiveSessionId,
    setPendingRequest,
    updateMessageInSession,
  };
}
