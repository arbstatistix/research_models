import React from 'react';
import { Button } from '../ui/Button';

interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (prompt: string) => void;
  onClear: () => void;
  isLoading: boolean;
  progressMessage?: string | null;
}

export const PromptInput: React.FC<PromptInputProps> = ({
  value,
  onChange,
  onSubmit,
  onClear,
  isLoading,
  progressMessage,
}) => {
  const [localValue, setLocalValue] = React.useState(value);

  React.useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (localValue.trim() && !isLoading) {
      onSubmit(localValue.trim());
    }
  };

  const handleClear = () => {
    setLocalValue('');
    onChange('');
    onClear();
  };

  return (
    <form onSubmit={handleSubmit} className="prompt-input-form">
      <div className="prompt-input-wrapper">
        <textarea
          value={localValue}
          onChange={(e) => {
            setLocalValue(e.target.value);
            onChange(e.target.value);
          }}
          placeholder="Enter your quantitative research question..."
          className="prompt-textarea"
          rows={4}
          disabled={isLoading}
        />
      </div>
      {isLoading && progressMessage && (
        <div className="progress-message">
          <span className="progress-spinner">⟳</span>
          {progressMessage}
        </div>
      )}
      
      <div className="prompt-actions">
        <Button
          type="submit"
          disabled={!localValue.trim() || isLoading}
          variant="primary"
        >
          {isLoading ? 'Processing...' : 'Submit'}
        </Button>
        <Button
          type="button"
          onClick={handleClear}
          disabled={isLoading}
          variant="secondary"
        >
          Clear
        </Button>
      </div>
    </form>
  );
};
