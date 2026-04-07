import React from 'react';
import { PromptInput } from '../components/pipeline/PromptInput';
import { OutputPanel } from '../components/pipeline/OutputPanel';
import { HistoryPanel } from '../components/pipeline/HistoryPanel';
import { StatusBadge } from '../components/pipeline/StatusBadge';
import { usePipeline } from '../hooks/usePipeline';
import type { HistoryItem } from '../types/pipeline';

interface HomeProps {
  history: HistoryItem[];
  onAddToHistory: (item: HistoryItem) => void;
  onClearHistory: () => void;
}

export const Home: React.FC<HomeProps> = ({ history, onAddToHistory }) => {
  const { result, isLoading, error, progressMessage, executePipeline, reset } = usePipeline();

  const getStatus = (): 'idle' | 'running' | 'completed' | 'failed' => {
    if (isLoading) return 'running';
    if (error) return 'failed';
    if (result) return result.success ? 'completed' : 'failed';
    return 'idle';
  };

  const handleSubmit = async (prompt: string) => {
    reset();
    const response = await executePipeline(prompt);
    
    if (response) {
      onAddToHistory({
        id: Date.now().toString(),
        timestamp: Date.now(),
        prompt: prompt,
        success: response.success,
        answer: response.success ? response.final_answer : null,
        error: !response.success ? (response.error || 'Unknown error') : null,
      });
    }
  };

  const handleClear = () => {
    reset();
  };

  return (
    <div className="home">
      <div className="home-content">
        <div className="home-main">
          <div className="status-bar">
            <span className="status-label">Pipeline Status</span>
            <StatusBadge status={getStatus()} />
          </div>
          
          <PromptInput
            value=""
            onChange={() => {}}
            onSubmit={handleSubmit}
            onClear={handleClear}
            isLoading={isLoading}
            progressMessage={progressMessage}
          />
          
          <OutputPanel result={result} error={error} />
        </div>
        
        <div className="home-sidebar">
          <HistoryPanel history={history} />
        </div>
      </div>
    </div>
  );
};
