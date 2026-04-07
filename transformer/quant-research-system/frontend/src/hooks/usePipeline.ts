import { useState, useCallback } from 'react';
import { submitResearchPrompt, cancelCurrentRequest } from '../services/api';
import type { PipelineResponse } from '../types/pipeline';

interface UsePipelineReturn {
  result: PipelineResponse | null;
  isLoading: boolean;
  error: string | null;
  progressMessage: string | null;
  executePipeline: (prompt: string) => Promise<PipelineResponse | null>;
  cancel: () => void;
  reset: () => void;
}

export function usePipeline(): UsePipelineReturn {
  const [result, setResult] = useState<PipelineResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progressMessage, setProgressMessage] = useState<string | null>(null);

  const executePipeline = useCallback(async (
    prompt: string
  ): Promise<PipelineResponse | null> => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setProgressMessage('Connecting to backend...');

    try {
      const response = await submitResearchPrompt({ prompt }, (msg) => {
        setProgressMessage(msg);
      });
      
      setResult(response);
      setProgressMessage(null);
      
      // If the pipeline itself reports failure, treat it as an error
      if (!response.success) {
        setError(response.error || 'Pipeline execution failed');
      }
      
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
      setError(errorMessage);
      setProgressMessage(null);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const cancel = useCallback(() => {
    cancelCurrentRequest();
    setIsLoading(false);
    setProgressMessage(null);
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setIsLoading(false);
    setError(null);
    setProgressMessage(null);
  }, []);

  return {
    result,
    isLoading,
    error,
    progressMessage,
    executePipeline,
    cancel,
    reset,
  };
}
