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

export interface HistoryItem {
  id: string;
  timestamp: number;
  prompt: string;
  success: boolean;
  answer: string | null;
  error: string | null;
}
