# Frontend Source

React application source code.

## Directory Structure

```
src/
├── main.tsx            # React entry point (renders App)
├── App.tsx             # Root component (composes main UI)
├── index.css           # Global styles and CSS variables
├── components/         # React components
├── hooks/              # Custom React hooks
├── services/           # External API calls
└── types/              # TypeScript type definitions
```

## Entry Point Flow

```
index.html
    │
    └── <script type="module" src="/src/main.tsx">
            │
            └── main.tsx
                    │
                    └── ReactDOM.createRoot().render(<App />)
                            │
                            └── App.tsx
                                    │
                                    ├── BloombergQuantTerminal
                                    └── PIDManager
```

## Module Responsibilities

### main.tsx
- Mounts React app to DOM
- Imports global CSS
- Wraps app in StrictMode

### App.tsx
- Composes main layout
- Renders BloombergQuantTerminal
- Renders PIDManager overlay

### index.css
- CSS reset/normalize
- Color variables
- Global typography
- Scrollbar styling
- KaTeX overrides

## Component Organization

### By Function

```
components/
├── BloombergQuantTerminal.tsx  # Main app component
├── PIDManager.tsx              # Process management
├── chat/                       # Chat-specific components
│   └── ChatSidebar.tsx         # Session list
├── pipeline/                   # Pipeline display
│   ├── StatusBadge.tsx
│   ├── HistoryPanel.tsx
│   ├── OutputPanel.tsx
│   └── PromptInput.tsx
├── layout/                     # Layout components
│   ├── Container.tsx
│   └── Header.tsx
└── ui/                         # Reusable UI
    ├── Button.tsx
    └── Card.tsx
```

### By Layer

```
┌─────────────────────────────────────────────┐
│                 App.tsx                      │
│  (Root component, composes everything)       │
└─────────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
┌───────┐     ┌──────────┐    ┌──────────┐
│ hooks │     │components│    │ services │
│       │     │          │    │          │
│ state │ ←── │   UI     │ ──→│   API    │
│ logic │     │ render   │    │  calls   │
└───────┘     └──────────┘    └──────────┘
                    │
                    ▼
              ┌──────────┐
              │  types   │
              │          │
              │TypeScript│
              │  types   │
              └──────────┘
```

## State Management

### Local State (useState)
- Current input text
- Loading state
- Error messages
- UI toggles

### Persisted State (useChatHistory hook)
- Chat sessions → localStorage
- Active session ID → localStorage
- Pending requests → localStorage

### Derived State (useMemo)
- Active session messages
- Filtered/sorted sessions
- Preprocessed markdown

## Data Flow

```
User Action (type, click, etc.)
         │
         ▼
Event Handler (onClick, onChange)
         │
         ▼
State Update (setState, hook function)
         │
         ▼
Re-render (React reconciliation)
         │
         ▼
DOM Update (visible change)
```

## Import Conventions

```typescript
// React imports first
import { useState, useEffect, useCallback } from 'react';

// External libraries
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// Internal components
import { ChatSidebar } from './chat/ChatSidebar';

// Hooks
import { useChatHistory } from '../hooks/useChatHistory';

// Services
import { submitResearchPrompt } from '../services/api';

// Types
import type { ChatMessage, PipelineResponse } from '../types/chat';

// Styles
import './index.css';
```

## File Naming Conventions

- **Components**: PascalCase (`BloombergTerminal.tsx`)
- **Hooks**: camelCase with `use` prefix (`useChatHistory.ts`)
- **Services**: camelCase (`api.ts`)
- **Types**: camelCase (`chat.ts`)
- **CSS**: kebab-case (`index.css`)
