// ============================================================================
// BLOOMBERG COLOR PALETTE - Shared across components
// ============================================================================
export const COLORS = {
  bgPrimary: '#000000',
  bgSecondary: '#0a0a0a',
  bgPanel: '#111111',
  bgHeader: '#1a1a1a',
  bgInput: '#0d0d0d',
  bgHover: '#1f1f1f',
  bgActive: '#2a2a2a',
  amber: '#FFA028',
  orange: '#FB8B1E',
  green: '#00D084',
  red: '#FF4757',
  blue: '#4A9EFF',
  cyan: '#00D4AA',
  textPrimary: '#FFFFFF',
  textSecondary: '#B0B0B0',
  textMuted: '#666666',
  border: '#222222',
  borderActive: '#FFA028',
} as const;

// ============================================================================
// MESSAGE TYPES
// ============================================================================
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

// ============================================================================
// PIPELINE TYPES (existing)
// ============================================================================
export interface PromptRequest {
  prompt: string;
}

export interface PipelineSuccessResponse {
  success: true;
  used_refinement: boolean;
  original_prompt: string;
  prompt_sent_to_researcher: string;
  final_answer: string;
  error_type?: null;
  error?: null;
  status_code?: null;
  traceback?: null;
}

export interface PipelineErrorResponse {
  success: false;
  used_refinement: boolean;
  original_prompt: string;
  prompt_sent_to_researcher: string;
  final_answer: null;
  error_type: string;
  error: string;
  status_code?: number | null;
  traceback?: string | null;
}

export type PipelineResponse = PipelineSuccessResponse | PipelineErrorResponse;

// Legacy HistoryItem (kept for backward compatibility)
export interface HistoryItem {
  id: string;
  timestamp: number;
  prompt: string;
  success: boolean;
  answer: string | null;
  error: string | null;
}
