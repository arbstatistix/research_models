import React from 'react';

type Status = 'idle' | 'running' | 'completed' | 'failed';

interface StatusBadgeProps {
  status: Status;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const statusConfig: Record<Status, { label: string; className: string }> = {
    idle: { label: 'Idle', className: 'status-idle' },
    running: { label: 'Running', className: 'status-running' },
    completed: { label: 'Completed', className: 'status-completed' },
    failed: { label: 'Failed', className: 'status-failed' },
  };

  const config = statusConfig[status];

  return (
    <div className={`status-badge ${config.className}`}>
      <span className="status-dot"></span>
      <span className="status-label">{config.label}</span>
    </div>
  );
};
