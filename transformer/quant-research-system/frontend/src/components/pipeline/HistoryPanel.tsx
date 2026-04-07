import React from 'react';
import { Card } from '../ui/Card';
import { HistoryItem } from '../../types/pipeline';

interface HistoryPanelProps {
  history: HistoryItem[];
}

export const HistoryPanel: React.FC<HistoryPanelProps> = ({ history }) => {
  if (history.length === 0) {
    return (
      <Card title="Request History" className="history-panel empty">
        <div className="empty-state">
          <p>No requests yet</p>
        </div>
      </Card>
    );
  }

  const formatTimestamp = (timestamp: number): string => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const truncateText = (text: string, maxLength: number = 100): string => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <Card title="Request History" className="history-panel">
      <div className="history-list">
        {[...history].reverse().map((item, index) => (
          <div
            key={item.id}
            className={`history-item ${item.success ? 'success' : 'error'}`}
          >
            <div className="history-header">
              <span className="history-number">#{history.length - index}</span>
              <span className="history-time">{formatTimestamp(item.timestamp)}</span>
              <span className={`history-status ${item.success ? 'success' : 'error'}`}>
                {item.success ? '✓' : '✗'}
              </span>
            </div>
            <div className="history-prompt">
              <strong>Prompt:</strong> {truncateText(item.prompt)}
            </div>
            {item.success ? (
              <div className="history-answer">
                <strong>Answer:</strong> {truncateText(item.answer || '', 150)}
              </div>
            ) : (
              <div className="history-error">
                <strong>Error:</strong> {truncateText(item.error || 'Unknown error')}
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};
