# Frontend - Quant Research Terminal

React + TypeScript frontend with a Bloomberg Terminal-inspired interface.

## Directory Structure

```
frontend/
├── index.html              # HTML entry point
├── package.json            # Dependencies and scripts
├── vite.config.ts          # Vite build configuration
├── tsconfig.json           # TypeScript configuration
└── src/
    ├── main.tsx            # React entry point
    ├── App.tsx             # Root component
    ├── index.css           # Global styles
    ├── components/         # React components
    │   ├── BloombergQuantTerminal.tsx  # Main terminal UI
    │   ├── PIDManager.tsx              # Process manager widget
    │   ├── chat/                       # Chat components
    │   ├── pipeline/                   # Pipeline display components
    │   ├── layout/                     # Layout components
    │   └── ui/                         # Reusable UI components
    ├── hooks/              # Custom React hooks
    │   ├── useChatHistory.ts   # Session persistence
    │   └── usePipeline.ts      # API integration
    ├── services/           # API client
    │   └── api.ts          # Backend API calls
    └── types/              # TypeScript definitions
        ├── chat.ts         # Chat types
        └── pipeline.ts     # Pipeline types
```

## Component Architecture

```
App.tsx
  │
  ├── BloombergQuantTerminal.tsx (Main UI)
  │   │
  │   ├── ChatSidebar (Session list)
  │   │   └── Session items (click to load)
  │   │
  │   ├── Header (Title, status indicator)
  │   │
  │   ├── Message List (Chat history)
  │   │   ├── User messages
  │   │   └── Assistant messages (with markdown)
  │   │
  │   └── Input Area (Prompt input, submit button)
  │
  └── PIDManager.tsx (Floating widget)
      ├── Toggle button
      └── Process list panel
```

## Data Flow

### Message Submission

```
1. User types prompt in input
   │
   ▼
2. Submit button clicked
   │
   ▼
3. Create user message in chat history
   │
   ▼
4. Call api.submitResearchPrompt()
   │
   ▼
5. Show loading state
   │
   ▼
6. Backend processes (30-120 seconds)
   │
   ▼
7. Receive PipelineResponse
   │
   ▼
8. Create assistant message with final_answer
   │
   ▼
9. Render markdown with LaTeX support
```

### Session Persistence

```
localStorage
    │
    ├── quant-research-chat-sessions  ← Array of sessions
    ├── quant-research-active-session ← Current session ID
    └── quant-research-pending-request ← Request in progress
    
useChatHistory hook manages:
    - Load on mount
    - Save on change
    - Create/delete sessions
    - Add messages to sessions
```

## Key Components

### BloombergQuantTerminal.tsx

Main terminal component with:
- Dark theme styling
- Chat message list
- Markdown rendering with LaTeX
- Input area with submit
- Loading state management

### PIDManager.tsx

Floating process manager:
- Shows count of active processes
- Lists process details (model, CPU, memory)
- Kill buttons for each process
- Auto-refresh every 3 seconds

### ChatSidebar.tsx

Session management:
- List of past sessions
- Click to load session
- Delete session button
- "New Chat" button

## Markdown Rendering

Uses react-markdown with plugins:
- `remark-gfm` - GitHub Flavored Markdown
- `remark-math` - Math syntax detection
- `rehype-katex` - LaTeX rendering
- `rehype-sanitize` - XSS protection

### LLM Output Preprocessing

```typescript
function preprocessLLMOutput(text: string): string {
    // Remove conversation tokens
    // Remove duplicate lines
    // Fix malformed tables
    // Clean excessive whitespace
}
```

## API Integration

### api.ts

```typescript
// Submit research prompt
const response = await submitResearchPrompt(
    { prompt: "What is arbitrage?" },
    (message) => console.log(message)  // Progress callback
);

// Cancel current request
cancelCurrentRequest();
```

### Error Handling

```typescript
try {
    const response = await submitResearchPrompt(request);
    if (response.success) {
        // Handle success
    } else {
        // Handle pipeline error
        showError(response.error);
    }
} catch (error) {
    // Handle network/timeout error
    showError(error.message);
}
```

## Styling

### Theme

Bloomberg Terminal-inspired dark theme:
- Background: `#0a0a0f`
- Text: `#e8e8e8`
- Accent: `#ff8c00` (orange)
- Success: `#00ff00`
- Error: `#ff4444`

### CSS Structure

```css
/* Global styles in index.css */
:root {
    --bg-primary: #0a0a0f;
    --text-primary: #e8e8e8;
    --accent: #ff8c00;
}

/* Component-specific styles in JSX */
<div style={{ background: COLORS.bg_primary }}>
```

## Running

```bash
# Development
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## TypeScript Types

### Chat Types (types/chat.ts)

```typescript
interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: number;
}

interface ChatSession {
    id: string;
    title: string;
    messages: ChatMessage[];
    createdAt: number;
    updatedAt: number;
}
```

### Pipeline Types (types/pipeline.ts)

```typescript
interface PromptRequest {
    prompt: string;
}

interface PipelineResponse {
    success: boolean;
    used_refinement: boolean;
    original_prompt: string;
    prompt_sent_to_researcher: string;
    final_answer: string;
    error_type?: string;
    error?: string;
}
```
