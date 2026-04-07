import React, { useState, useEffect, useRef } from 'react';
import 'katex/dist/katex.min.css';

// ============================================================================
// BLOOMBERG TERMINAL COLOR PALETTE
// ============================================================================
const COLORS = {
  // Backgrounds
  bgPrimary: '#000000',
  bgSecondary: '#0a0a0a',
  bgPanel: '#111111',
  bgHeader: '#1a1a1a',
  bgInput: '#0d0d0d',
  
  // Bloomberg Signature Colors
  amber: '#FFA028',
  amberDark: '#CC7A1E',
  orange: '#FB8B1E',
  
  // Data Colors
  green: '#00D084',
  greenDim: '#00A868',
  red: '#FF4757',
  redDim: '#CC3845',
  
  // Accents
  blue: '#4A9EFF',
  blueDim: '#3A7ECC',
  cyan: '#00D4AA',
  magenta: '#FF6B9D',
  
  // Text
  textPrimary: '#FFFFFF',
  textSecondary: '#B0B0B0',
  textMuted: '#666666',
  textDisabled: '#444444',
  
  // Borders
  border: '#222222',
  borderActive: '#FFA028',
  
  // Status
  statusRunning: '#4A9EFF',
  statusSuccess: '#00D084',
  statusError: '#FF4757',
  statusIdle: '#666666',
};

// ============================================================================
// TYPES
// ============================================================================
interface WatchlistItem {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePct: number;
  volume: string;
  high: number;
  low: number;
}

interface NewsItem {
  time: string;
  source: string;
  headline: string;
  urgent: boolean;
}

interface HistoryItem {
  id: string;
  time: string;
  prompt: string;
  status: 'idle' | 'running' | 'success' | 'error';
  duration: string;
}

interface PipelineResult {
  success: boolean;
  used_refinement: boolean;
  prompt_sent_to_researcher?: string;
  final_answer: string;
}

// ============================================================================
// MOCK DATA
// ============================================================================
const MOCK_WATCHLIST: WatchlistItem[] = [
  { symbol: 'SPX', name: 'S&P 500', price: 4523.67, change: 12.45, changePct: 0.28, volume: '2.1B', high: 4531.20, low: 4512.89 },
  { symbol: 'NDX', name: 'Nasdaq 100', price: 15678.90, change: -45.23, changePct: -0.29, volume: '4.5B', high: 15734.56, low: 15612.34 },
  { symbol: 'VIX', name: 'Volatility Index', price: 14.23, change: -0.45, changePct: -3.07, volume: '125M', high: 15.12, low: 13.98 },
  { symbol: 'EURUSD', name: 'EUR/USD', price: 1.0845, change: 0.0012, changePct: 0.11, volume: '89B', high: 1.0867, low: 1.0823 },
  { symbol: 'BTC', name: 'Bitcoin', price: 67432.50, change: 1234.67, changePct: 1.87, volume: '34B', high: 68123.00, low: 66123.45 },
  { symbol: 'ETH', name: 'Ethereum', price: 3456.78, change: -23.45, changePct: -0.67, volume: '15B', high: 3512.90, low: 3423.12 },
  { symbol: 'GLD', name: 'Gold', price: 2034.50, change: 8.90, changePct: 0.44, volume: '12B', high: 2045.60, low: 2023.40 },
  { symbol: 'CL1', name: 'Crude Oil', price: 78.45, change: -1.23, changePct: -1.54, volume: '890M', high: 80.12, low: 77.89 },
];

const MOCK_NEWS: NewsItem[] = [
  { time: '14:32', source: 'BLOOM', headline: 'Fed signals potential rate pause in June meeting minutes', urgent: true },
  { time: '14:28', source: 'RTRS', headline: 'Tech sector leads rally as AI earnings beat expectations', urgent: false },
  { time: '14:15', source: 'BLOOM', headline: 'Oil prices decline on inventory build concerns', urgent: false },
  { time: '14:02', source: 'DJ', headline: 'European markets close higher on manufacturing data', urgent: false },
  { time: '13:45', source: 'BLOOM', headline: 'Treasury yields rise ahead of auction', urgent: false },
];

const MOCK_HISTORY: HistoryItem[] = [
  { id: '001', time: '14:30:15', prompt: 'Black-Scholes Greeks calculation', status: 'success', duration: '2.3s' },
  { id: '002', time: '14:28:42', prompt: 'Monte Carlo VaR estimation', status: 'success', duration: '4.1s' },
  { id: '003', time: '14:25:10', prompt: 'GARCH(1,1) parameter estimation', status: 'error', duration: '1.8s' },
  { id: '004', time: '14:22:33', prompt: 'Kalman filter state-space model', status: 'success', duration: '3.5s' },
  { id: '005', time: '14:18:55', prompt: 'Mean-variance optimization', status: 'success', duration: '2.7s' },
];

// ============================================================================
// UTILITY COMPONENTS
// ============================================================================

interface FormatNumberProps {
  value: number;
  decimals?: number;
  prefix?: string;
}

const FormatNumber: React.FC<FormatNumberProps> = ({ value, decimals = 2, prefix = '' }) => {
  const formatted = typeof value === 'number' 
    ? value.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
    : value;
  return <span>{prefix}{formatted}</span>;
};

interface ChangeIndicatorProps {
  value: number;
  suffix?: string;
}

const ChangeIndicator: React.FC<ChangeIndicatorProps> = ({ value, suffix = '' }) => {
  const isPositive = value >= 0;
  const color = isPositive ? COLORS.green : COLORS.red;
  const sign = isPositive ? '+' : '';
  return (
    <span style={{ color }}>
      {sign}{value.toFixed(2)}{suffix}
    </span>
  );
};

interface StatusDotProps {
  status: 'idle' | 'running' | 'success' | 'error';
}

const StatusDot: React.FC<StatusDotProps> = ({ status }) => {
  const colors = {
    idle: COLORS.statusIdle,
    running: COLORS.statusRunning,
    success: COLORS.statusSuccess,
    error: COLORS.statusError,
  };
  return (
    <span 
      style={{ 
        display: 'inline-block',
        width: 8, 
        height: 8, 
        borderRadius: '50%', 
        backgroundColor: colors[status] || colors.idle,
        marginRight: 6,
        animation: status === 'running' ? 'pulse 1s infinite' : 'none'
      }} 
    />
  );
};

// ============================================================================
// PANEL COMPONENTS
// ============================================================================

interface PanelProps {
  title?: string;
  children: React.ReactNode;
  active?: boolean;
  className?: string;
}

const Panel: React.FC<PanelProps> = ({ title, children, active = false, className = '' }) => (
  <div 
    className={className}
    style={{ 
      backgroundColor: COLORS.bgPanel,
      border: `1px solid ${active ? COLORS.borderActive : COLORS.border}`,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      height: '100%'
    }}
  >
    {title && (
      <div style={{ 
        backgroundColor: COLORS.bgHeader,
        padding: '4px 8px',
        borderBottom: `1px solid ${COLORS.border}`,
        fontSize: '11px',
        fontWeight: 600,
        color: active ? COLORS.amber : COLORS.textSecondary,
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <span>{title}</span>
        {active && <span style={{ color: COLORS.amber, fontSize: '9px' }}>● LIVE</span>}
      </div>
    )}
    <div style={{ flex: 1, overflow: 'auto' }}>
      {children}
    </div>
  </div>
);

const WatchlistPanel: React.FC = () => (
  <Panel title="WATCHLIST" active>
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
      <thead>
        <tr style={{ backgroundColor: COLORS.bgHeader, color: COLORS.textSecondary, fontSize: '10px' }}>
          <th style={{ padding: '4px 6px', textAlign: 'left' }}>SYMBOL</th>
          <th style={{ padding: '4px 6px', textAlign: 'right' }}>LAST</th>
          <th style={{ padding: '4px 6px', textAlign: 'right' }}>CHG</th>
          <th style={{ padding: '4px 6px', textAlign: 'right' }}>%CHG</th>
          <th style={{ padding: '4px 6px', textAlign: 'right' }}>VOL</th>
        </tr>
      </thead>
      <tbody>
        {MOCK_WATCHLIST.map((item, idx) => (
          <tr 
            key={item.symbol}
            style={{ 
              borderBottom: `1px solid ${COLORS.border}`,
              backgroundColor: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)'
            }}
          >
            <td style={{ padding: '3px 6px' }}>
              <span style={{ color: COLORS.amber, fontWeight: 600 }}>{item.symbol}</span>
              <span style={{ color: COLORS.textMuted, fontSize: '10px', marginLeft: 4 }}>{item.name}</span>
            </td>
            <td style={{ padding: '3px 6px', textAlign: 'right', color: COLORS.textPrimary, fontFamily: 'monospace' }}>
              <FormatNumber value={item.price} />
            </td>
            <td style={{ padding: '3px 6px', textAlign: 'right', fontFamily: 'monospace' }}>
              <ChangeIndicator value={item.change} />
            </td>
            <td style={{ padding: '3px 6px', textAlign: 'right', fontFamily: 'monospace' }}>
              <ChangeIndicator value={item.changePct} suffix="%" />
            </td>
            <td style={{ padding: '3px 6px', textAlign: 'right', color: COLORS.textSecondary, fontSize: '11px' }}>
              {item.volume}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </Panel>
);

const NewsPanel: React.FC = () => (
  <Panel title="NEWS">
    <div style={{ padding: '4px 0' }}>
      {MOCK_NEWS.map((news, idx) => (
        <div 
          key={idx}
          style={{ 
            padding: '6px 8px',
            borderBottom: `1px solid ${COLORS.border}`,
            fontSize: '11px',
            backgroundColor: news.urgent ? 'rgba(255, 71, 87, 0.1)' : 'transparent'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
            <span style={{ color: COLORS.amber, fontWeight: 600, fontSize: '10px' }}>{news.time}</span>
            <span style={{ 
              color: news.urgent ? COLORS.red : COLORS.blue,
              fontSize: '9px',
              fontWeight: 600,
              padding: '1px 4px',
              backgroundColor: news.urgent ? 'rgba(255, 71, 87, 0.2)' : 'rgba(74, 158, 255, 0.2)'
            }}>
              {news.source}
            </span>
            {news.urgent && <span style={{ color: COLORS.red, fontSize: '9px' }}>URGENT</span>}
          </div>
          <div style={{ color: COLORS.textPrimary, lineHeight: 1.4 }}>{news.headline}</div>
        </div>
      ))}
    </div>
  </Panel>
);

const HistoryPanel: React.FC = () => (
  <Panel title="REQUEST HISTORY">
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px' }}>
      <thead>
        <tr style={{ backgroundColor: COLORS.bgHeader, color: COLORS.textSecondary, fontSize: '10px' }}>
          <th style={{ padding: '4px 6px', textAlign: 'left' }}>ID</th>
          <th style={{ padding: '4px 6px', textAlign: 'left' }}>TIME</th>
          <th style={{ padding: '4px 6px', textAlign: 'left' }}>QUERY</th>
          <th style={{ padding: '4px 6px', textAlign: 'center' }}>STATUS</th>
          <th style={{ padding: '4px 6px', textAlign: 'right' }}>DUR</th>
        </tr>
      </thead>
      <tbody>
        {MOCK_HISTORY.map((item, idx) => (
          <tr 
            key={item.id}
            style={{ 
              borderBottom: `1px solid ${COLORS.border}`,
              backgroundColor: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 160, 40, 0.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)';
            }}
          >
            <td style={{ padding: '4px 6px', color: COLORS.textMuted, fontFamily: 'monospace' }}>{item.id}</td>
            <td style={{ padding: '4px 6px', color: COLORS.amber, fontFamily: 'monospace', fontSize: '10px' }}>{item.time}</td>
            <td style={{ padding: '4px 6px', color: COLORS.textPrimary, maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {item.prompt}
            </td>
            <td style={{ padding: '4px 6px', textAlign: 'center' }}>
              <StatusDot status={item.status} />
              <span style={{ 
                color: item.status === 'success' ? COLORS.green : COLORS.red,
                fontSize: '10px',
                textTransform: 'uppercase'
              }}>
                {item.status}
              </span>
            </td>
            <td style={{ padding: '4px 6px', textAlign: 'right', color: COLORS.textSecondary, fontFamily: 'monospace' }}>
              {item.duration}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </Panel>
);

interface OutputPanelProps {
  result: PipelineResult | null;
  isLoading: boolean;
  progressMessage: string;
}

const OutputPanel: React.FC<OutputPanelProps> = ({ result, isLoading, progressMessage }) => {
  if (isLoading) {
    return (
      <Panel title="OUTPUT" active>
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column',
          alignItems: 'center', 
          justifyContent: 'center',
          height: '100%',
          padding: 20
        }}>
          <div style={{ 
            width: 40, 
            height: 40, 
            border: `2px solid ${COLORS.border}`,
            borderTop: `2px solid ${COLORS.amber}`,
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
          <p style={{ color: COLORS.amber, marginTop: 16, fontSize: '12px' }}>
            {progressMessage || 'PROCESSING...'}
          </p>
          <p style={{ color: COLORS.textMuted, fontSize: '11px', marginTop: 8 }}>
            Model inference in progress
          </p>
        </div>
      </Panel>
    );
  }

  if (!result) {
    return (
      <Panel title="OUTPUT">
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          height: '100%',
          color: COLORS.textMuted,
          fontSize: '12px'
        }}>
          <div style={{ textAlign: 'center' }}>
            <p>READY FOR INPUT</p>
            <p style={{ fontSize: '11px', marginTop: 8 }}>Enter a quantitative research query</p>
          </div>
        </div>
      </Panel>
    );
  }

  return (
    <Panel title="OUTPUT" active>
      <div style={{ padding: 12, fontSize: '13px', lineHeight: 1.7 }}>
        {result.used_refinement && (
          <div style={{ 
            marginBottom: 16, 
            padding: 8, 
            backgroundColor: 'rgba(74, 158, 255, 0.1)',
            borderLeft: `3px solid ${COLORS.blue}`,
            fontSize: '11px'
          }}>
            <span style={{ color: COLORS.blue, fontWeight: 600 }}>REFINED QUERY:</span>
            <p style={{ color: COLORS.textSecondary, marginTop: 4 }}>{result.prompt_sent_to_researcher}</p>
          </div>
        )}
        
        <div className="latex-content" style={{ color: COLORS.textPrimary, whiteSpace: 'pre-wrap' }}>
          {result.final_answer}
        </div>
      </div>
    </Panel>
  );
};

const MetricsPanel: React.FC = () => (
  <Panel title="SYSTEM METRICS">
    <div style={{ padding: 8, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
      <div style={{ 
        padding: 8, 
        backgroundColor: COLORS.bgSecondary,
        border: `1px solid ${COLORS.border}`
      }}>
        <div style={{ fontSize: '10px', color: COLORS.textMuted, textTransform: 'uppercase' }}>CPU Usage</div>
        <div style={{ fontSize: '18px', color: COLORS.green, fontFamily: 'monospace', marginTop: 4 }}>34.2%</div>
        <div style={{ fontSize: '10px', color: COLORS.textSecondary, marginTop: 2 }}>8 cores active</div>
      </div>
      
      <div style={{ 
        padding: 8, 
        backgroundColor: COLORS.bgSecondary,
        border: `1px solid ${COLORS.border}`
      }}>
        <div style={{ fontSize: '10px', color: COLORS.textMuted, textTransform: 'uppercase' }}>Memory</div>
        <div style={{ fontSize: '18px', color: COLORS.amber, fontFamily: 'monospace', marginTop: 4 }}>12.4GB</div>
        <div style={{ fontSize: '10px', color: COLORS.textSecondary, marginTop: 2 }}>of 32GB total</div>
      </div>
      
      <div style={{ 
        padding: 8, 
        backgroundColor: COLORS.bgSecondary,
        border: `1px solid ${COLORS.border}`
      }}>
        <div style={{ fontSize: '10px', color: COLORS.textMuted, textTransform: 'uppercase' }}>GPU Util</div>
        <div style={{ fontSize: '18px', color: COLORS.cyan, fontFamily: 'monospace', marginTop: 4 }}>78%</div>
        <div style={{ fontSize: '10px', color: COLORS.textSecondary, marginTop: 2 }}>CUDA active</div>
      </div>
      
      <div style={{ 
        padding: 8, 
        backgroundColor: COLORS.bgSecondary,
        border: `1px solid ${COLORS.border}`
      }}>
        <div style={{ fontSize: '10px', color: COLORS.textMuted, textTransform: 'uppercase' }}>Queue</div>
        <div style={{ fontSize: '18px', color: COLORS.textPrimary, fontFamily: 'monospace', marginTop: 4 }}>0</div>
        <div style={{ fontSize: '10px', color: COLORS.textSecondary, marginTop: 2 }}>requests pending</div>
      </div>
    </div>
    
    <div style={{ padding: '0 8px 8px' }}>
      <div style={{ 
        padding: 8, 
        backgroundColor: COLORS.bgSecondary,
        border: `1px solid ${COLORS.border}`,
        fontSize: '11px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span style={{ color: COLORS.textMuted }}>Model:</span>
          <span style={{ color: COLORS.amber }}>qwen3.5:latest</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span style={{ color: COLORS.textMuted }}>Temp:</span>
          <span style={{ color: COLORS.textPrimary }}>0.20</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: COLORS.textMuted }}>Max Tokens:</span>
          <span style={{ color: COLORS.textPrimary }}>4096</span>
        </div>
      </div>
    </div>
  </Panel>
);

// ============================================================================
// MAIN TERMINAL COMPONENT
// ============================================================================

const BloombergTerminal: React.FC = () => {
  const [command, setCommand] = useState('');
  const [activePanel, setActivePanel] = useState('output');
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [progressMessage, setProgressMessage] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date());
  
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim()) return;
    
    setIsLoading(true);
    setProgressMessage('Initializing inference...');
    
    setTimeout(() => {
      setProgressMessage('Running model...');
      setTimeout(() => {
        setResult({
          success: true,
          used_refinement: true,
          prompt_sent_to_researcher: `Calculate the Black-Scholes option price for a European call option with strike $K = 100$, spot $S_0 = 105$, volatility $\\sigma = 0.2$, risk-free rate $r = 0.05$, time to maturity $T = 1$ year.`,
          final_answer: `## Black-Scholes Option Pricing

The Black-Scholes formula for a European call option is:

$$C = S_0 N(d_1) - K e^{-rT} N(d_2)$$

Where:

$$d_1 = \\frac{\\ln(S_0/K) + (r + \\sigma^2/2)T}{\\sigma\\sqrt{T}}$$

$$d_2 = d_1 - \\sigma\\sqrt{T}$$

### Given Parameters:
- Spot price: $S_0 = 105$
- Strike price: $K = 100$
- Volatility: $\\sigma = 0.20$
- Risk-free rate: $r = 0.05$
- Time to maturity: $T = 1.0$

### Calculation:

$$d_1 = \\frac{\\ln(105/100) + (0.05 + 0.2^2/2) \\times 1}{0.2 \\times \\sqrt{1}} = \\frac{0.0488 + 0.07}{0.2} = 0.594$$

$$d_2 = 0.594 - 0.2 = 0.394$$

Using the standard normal CDF:
- $N(d_1) = N(0.594) = 0.724$
- $N(d_2) = N(0.394) = 0.653$

### Final Price:

$$C = 105 \\times 0.724 - 100 \\times e^{-0.05} \\times 0.653$$
$$C = 76.02 - 62.08 = \\boxed{13.94}$$

The theoretical price of the European call option is **$13.94**.`
        });
        setIsLoading(false);
        setProgressMessage('');
      }, 2000);
    }, 1000);
    
    setCommand('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setCommand('');
    }
  };

  return (
    <div 
      style={{ 
        width: '100vw', 
        height: '100vh', 
        backgroundColor: COLORS.bgPrimary,
        color: COLORS.textPrimary,
        fontFamily: '"Segoe UI", "Roboto Mono", "Consolas", monospace',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}
    >
      {/* TOP COMMAND BAR */}
      <div style={{ 
        backgroundColor: COLORS.bgHeader,
        borderBottom: `2px solid ${COLORS.amber}`,
        padding: '6px 12px',
        display: 'flex',
        alignItems: 'center',
        gap: 12
      }}>
        <div style={{ 
          backgroundColor: COLORS.amber,
          color: COLORS.bgPrimary,
          padding: '4px 8px',
          fontWeight: 800,
          fontSize: '12px',
          letterSpacing: '1px'
        }}>
          QUANT
        </div>
        
        <form onSubmit={handleSubmit} style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ color: COLORS.amber, fontSize: '12px', fontWeight: 600 }}>&gt;</span>
          <input
            ref={inputRef}
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter command or research query..."
            style={{
              flex: 1,
              backgroundColor: 'transparent',
              border: 'none',
              color: COLORS.textPrimary,
              fontSize: '13px',
              fontFamily: 'inherit',
              outline: 'none',
              padding: '4px 0'
            }}
          />
        </form>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: '11px' }}>
          <span style={{ color: COLORS.textMuted }}>
            {currentTime.toLocaleTimeString('en-US', { hour12: false })}
          </span>
          <span style={{ color: COLORS.green }}>● CONNECTED</span>
          <span style={{ color: COLORS.amber }}>OLLAMA</span>
        </div>
      </div>

      {/* FUNCTION KEY BAR */}
      <div style={{ 
        backgroundColor: COLORS.bgSecondary,
        borderBottom: `1px solid ${COLORS.border}`,
        padding: '4px 12px',
        display: 'flex',
        gap: 4,
        fontSize: '10px'
      }}>
        {['1-MKT', '2-NEWS', '3-HIST', '4-OUT', '5-METRICS', '6-HELP'].map((label) => (
          <button
            key={label}
            onClick={() => setActivePanel(label.split('-')[1].toLowerCase())}
            style={{
              padding: '3px 10px',
              backgroundColor: activePanel === label.split('-')[1].toLowerCase() ? COLORS.amber : 'transparent',
              color: activePanel === label.split('-')[1].toLowerCase() ? COLORS.bgPrimary : COLORS.textSecondary,
              border: 'none',
              cursor: 'pointer',
              fontSize: '10px',
              fontWeight: 600
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* MAIN CONTENT GRID */}
      <div style={{ 
        flex: 1, 
        display: 'grid',
        gridTemplateColumns: '280px 1fr 320px',
        gridTemplateRows: '1fr 200px',
        gap: 2,
        padding: 2,
        overflow: 'hidden'
      }}>
        {/* LEFT COLUMN */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <div style={{ flex: 1 }}>
            <WatchlistPanel />
          </div>
          <div style={{ height: 200 }}>
            <NewsPanel />
          </div>
        </div>

        {/* CENTER COLUMN - OUTPUT */}
        <div style={{ gridRow: 'span 2' }}>
          <OutputPanel 
            result={result} 
            isLoading={isLoading}
            progressMessage={progressMessage}
          />
        </div>

        {/* RIGHT COLUMN */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2, gridRow: 'span 2' }}>
          <div style={{ flex: 1 }}>
            <HistoryPanel />
          </div>
          <div style={{ height: 240 }}>
            <MetricsPanel />
          </div>
        </div>
      </div>

      {/* BOTTOM STATUS BAR */}
      <div style={{ 
        backgroundColor: COLORS.bgHeader,
        borderTop: `1px solid ${COLORS.border}`,
        padding: '4px 12px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '10px'
      }}>
        <div style={{ display: 'flex', gap: 16 }}>
          <span style={{ color: COLORS.textMuted }}>
            <span style={{ color: COLORS.amber }}>F1</span> HELP 
            <span style={{ color: COLORS.amber, marginLeft: 8 }}>F5</span> REFRESH 
            <span style={{ color: COLORS.amber, marginLeft: 8 }}>ESC</span> CLEAR
          </span>
        </div>
        <div style={{ display: 'flex', gap: 16, color: COLORS.textSecondary }}>
          <span>Quant Research Pipeline v1.0</span>
          <span style={{ color: COLORS.green }}>System Normal</span>
        </div>
      </div>
    </div>
  );
};

export default BloombergTerminal;
