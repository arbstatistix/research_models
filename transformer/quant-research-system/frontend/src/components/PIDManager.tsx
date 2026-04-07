import { useState, useEffect, useCallback } from 'react';

interface PIDEntry {
  pid: number;
  type: string;
  model: string;
  prompt?: string;
  created_at: string;
  status: string;
  cpu_percent?: number;
  memory_mb?: number;
}

interface PIDResponse {
  success: boolean;
  count: number;
  pids: PIDEntry[];
}

export function PIDManager() {
  const [isOpen, setIsOpen] = useState(false);
  const [pids, setPids] = useState<PIDEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const API_BASE = 'http://localhost:8000/api';

  const fetchPIDs = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/pids`);
      if (!response.ok) throw new Error('Failed to fetch PIDs');
      const data: PIDResponse = await response.json();
      setPids(data.pids);
      setLastRefresh(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  }, []);

  const killPID = async (pid: number) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/pids/${pid}/kill`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to kill process');
      await fetchPIDs(); // Refresh list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const killAll = async () => {
    if (!confirm('Kill all tracked processes?')) return;
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/pids/kill-all`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to kill processes');
      await fetchPIDs(); // Refresh list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const killServer = async () => {
    if (!confirm('EMERGENCY: Kill the backend server? You will need to restart it manually.')) return;
    try {
      const response = await fetch(`${API_BASE}/server/kill`);
      if (!response.ok) throw new Error('Failed to kill server');
      alert('Server is shutting down...');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  // Auto-refresh when opened
  useEffect(() => {
    if (isOpen) {
      fetchPIDs();
      const interval = setInterval(fetchPIDs, 3000); // Refresh every 3s
      return () => clearInterval(interval);
    }
  }, [isOpen, fetchPIDs]);

  const runningCount = pids.filter(p => p.status === 'running').length;

  return (
    <div style={{ position: 'fixed', bottom: '20px', right: '20px', zIndex: 9999 }}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '50px',
          height: '50px',
          borderRadius: '50%',
          background: runningCount > 0 ? '#ff4444' : '#4444ff',
          color: 'white',
          border: '2px solid rgba(255,255,255,0.3)',
          cursor: 'pointer',
          fontSize: '18px',
          fontWeight: 'bold',
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.2s',
        }}
        title="Process Manager"
      >
        {runningCount > 0 ? `⚡${runningCount}` : '⚙️'}
      </button>

      {/* Panel */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            bottom: '60px',
            right: '0',
            width: '400px',
            maxHeight: '500px',
            background: 'rgba(20, 20, 30, 0.95)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '12px',
            padding: '16px',
            color: '#fff',
            fontFamily: 'monospace',
            fontSize: '12px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            overflow: 'auto',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 style={{ margin: 0, color: '#ffaa00' }}>🔧 Process Manager</h3>
            <button
              onClick={() => setIsOpen(false)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#fff',
                cursor: 'pointer',
                fontSize: '16px',
              }}
            >
              ✕
            </button>
          </div>

          {error && (
            <div style={{ 
              background: 'rgba(255, 0, 0, 0.2)', 
              padding: '8px', 
              borderRadius: '4px',
              marginBottom: '12px',
              color: '#ff6666'
            }}>
              ⚠️ {error}
            </div>
          )}

          <div style={{ marginBottom: '12px', display: 'flex', gap: '8px' }}>
            <button
              onClick={fetchPIDs}
              disabled={loading}
              style={{
                padding: '6px 12px',
                background: '#4444ff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '11px',
              }}
            >
              🔄 Refresh
            </button>
            {runningCount > 0 && (
              <button
                onClick={killAll}
                disabled={loading}
                style={{
                  padding: '6px 12px',
                  background: '#ff4444',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '11px',
                }}
              >
                💀 Kill All
              </button>
            )}
            <button
              onClick={killServer}
              style={{
                padding: '6px 12px',
                background: '#ff0000',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '11px',
                marginLeft: 'auto',
              }}
            >
              ☠️ Kill Server
            </button>
          </div>

          {lastRefresh && (
            <div style={{ color: '#888', fontSize: '10px', marginBottom: '8px' }}>
              Last updated: {lastRefresh.toLocaleTimeString()}
            </div>
          )}

          {pids.length === 0 ? (
            <div style={{ color: '#888', textAlign: 'center', padding: '20px' }}>
              No active processes
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {pids.map((pid) => (
                <div
                  key={pid.pid}
                  style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    padding: '10px',
                    borderRadius: '6px',
                    borderLeft: `3px solid ${pid.status === 'running' ? '#44ff44' : '#ff4444'}`,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 'bold', color: '#ffaa00' }}>
                      PID: {pid.pid}
                    </span>
                    <span style={{ 
                      color: pid.status === 'running' ? '#44ff44' : '#ff4444',
                      fontSize: '10px',
                      textTransform: 'uppercase'
                    }}>
                      {pid.status}
                    </span>
                  </div>
                  
                  <div style={{ marginTop: '4px', color: '#aaa' }}>
                    Type: {pid.type} | Model: {pid.model}
                  </div>
                  
                  {pid.cpu_percent !== undefined && (
                    <div style={{ marginTop: '4px', color: '#888', fontSize: '10px' }}>
                      CPU: {pid.cpu_percent.toFixed(1)}% | Memory: {pid.memory_mb?.toFixed(0)} MB
                    </div>
                  )}
                  
                  {pid.prompt && (
                    <div style={{ marginTop: '4px', color: '#666', fontSize: '10px', fontStyle: 'italic' }}>
                      "{pid.prompt}"
                    </div>
                  )}
                  
                  <div style={{ marginTop: '8px', display: 'flex', gap: '8px' }}>
                    <button
                      onClick={() => killPID(pid.pid)}
                      disabled={loading || pid.status !== 'running'}
                      style={{
                        padding: '4px 10px',
                        background: pid.status === 'running' ? '#ff4444' : '#444',
                        color: 'white',
                        border: 'none',
                        borderRadius: '3px',
                        cursor: pid.status === 'running' ? 'pointer' : 'not-allowed',
                        fontSize: '10px',
                      }}
                    >
                      Kill
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
