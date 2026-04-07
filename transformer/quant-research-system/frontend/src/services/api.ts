import type { PromptRequest, PipelineResponse } from '../types/pipeline';

const API_BASE_URL = 'http://localhost:8000';

// Abort controller for request cancellation
let currentController: AbortController | null = null;

export function cancelCurrentRequest(): void {
  if (currentController) {
    currentController.abort();
    currentController = null;
  }
}

export async function submitResearchPrompt(
  request: PromptRequest,
  onProgress?: (message: string) => void
): Promise<PipelineResponse> {
  // Cancel any existing request
  cancelCurrentRequest();
  
  // Create new abort controller
  currentController = new AbortController();
  
  // Update progress
  onProgress?.('Sending request to backend...');
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/research`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
      signal: currentController.signal,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || `HTTP error! status: ${response.status}`
      );
    }

    onProgress?.('Processing complete!');
    return response.json();
  } catch (error) {
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new Error('Request was cancelled');
      }
      if (error.message.includes('fetch')) {
        throw new Error('Network error: Backend may be busy or unavailable. The model can take 30-60 seconds to respond.');
      }
    }
    throw error;
  } finally {
    currentController = null;
  }
}
