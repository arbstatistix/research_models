import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import 'katex/dist/katex.min.css';
import { Card } from '../ui/Card';
import { PipelineResponse } from '../../types/pipeline';

interface OutputPanelProps {
  result: PipelineResponse | null;
  error: string | null;
}

// Extended sanitize schema for math elements
const sanitizeSchema = {
  ...defaultSchema,
  attributes: {
    ...defaultSchema.attributes,
    span: [...(defaultSchema.attributes?.span || []), 'className'],
    div: [...(defaultSchema.attributes?.div || []), 'className'],
  },
  tagNames: [
    ...(defaultSchema.tagNames || []),
    'math',
    'mrow',
    'mi',
    'mo',
    'mn',
    'mfrac',
    'msqrt',
    'msup',
    'msub',
    'msubsup',
    'mtext',
    'mspace',
    'mstyle',
  ],
};

/**
 * Aggressive cleanup of LLM output artifacts
 */
function preprocessLLMOutput(text: string): string {
  if (!text) return '';

  let cleaned = text;

  // Remove conversation/special tokens (common in fine-tuned models)
  cleaned = cleaned.replace(/<\|im_start\|>.*?<\|im_end\|>/gs, '');
  cleaned = cleaned.replace(/<\|im_start\|>/g, '');
  cleaned = cleaned.replace(/<\|im_end\|>/g, '');
  cleaned = cleaned.replace(/<\|endoftext\|>/g, '');
  cleaned = cleaned.replace(/assistant|user|system/g, '');

  // Remove repeated metadata headers
  cleaned = cleaned.replace(/^(#{1,6}\s*(?:Response|Answer|Output|Result|Final Answer)[:\s]*)+$/gim, '');
  cleaned = cleaned.replace(/^(?:Response|Answer|Output|Result|Final Answer)[:\s]*$/gim, '');

  // Remove excessive horizontal rules
  cleaned = cleaned.replace(/(?:^[-*_]{3,}\s*\n){2,}/gm, '---\n');

  // Remove timestamp spam, JSON metadata blocks
  const spamPatterns = [
    /\[\s*\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[^\]]*\]/g,
    /\{\s*"model"\s*:\s*"[^"]+"\s*,\s*"[^"]+"\s*:\s*[^}]+\}/g,
    /_{10,}/g,
    /\*{10,}/g,
    /-{10,}/g,
    /={10,}/g,
  ];
  spamPatterns.forEach((pattern) => {
    cleaned = cleaned.replace(pattern, '');
  });

  // DEDUPLICATION: Remove lines that are duplicates with/without LaTeX formatting
  // This handles cases where LLM outputs: "C(S,t)=..." then "C(S,t)=..." with subscripts
  const lines = cleaned.split('\n');
  const deduped: string[] = [];
  const seen = new Set<string>();

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      deduped.push('');
      continue;
    }

    // Normalize for comparison: remove LaTeX delimiters, subscript markers, extra spaces
    const normalized = trimmed
      .replace(/\$\$?/g, '')
      .replace(/[_^]\{([^}]+)\}/g, '$1')
      .replace(/[_^](\w)/g, '$1')
      .replace(/\\[a-zA-Z]+/g, '')
      .replace(/\\[\[\]()]/g, '')
      .replace(/[\s\u200B-\u200D\uFEFF]+/g, ' ')
      .replace(/[∗⋆]/g, '*')
      .trim()
      .toLowerCase();

    // Skip if we've seen this normalized form (and it's substantial content)
    if (normalized.length > 5 && seen.has(normalized)) {
      continue;
    }

    seen.add(normalized);
    deduped.push(line);
  }
  cleaned = deduped.join('\n');

  // Fix broken table separators (ensure proper |---| format)
  cleaned = cleaned.replace(/^(\|[-\s]+\|)+$/gm, (match) => {
    return match.replace(/\s+/g, '').replace(/\|/g, ' | ').trim();
  });

  // Normalize math delimiters: ensure proper spacing
  cleaned = cleaned.replace(/\$\$\s*/g, '$$$$\n');
  cleaned = cleaned.replace(/\s*\$\$/g, '\n$$$$');

  // Clean up excessive blank lines
  cleaned = cleaned.replace(/\n{4,}/g, '\n\n\n');

  // Trim whitespace
  return cleaned.trim();
}

/**
 * Custom markdown components with clean styling
 */
const markdownComponents: React.ComponentProps<typeof ReactMarkdown>['components'] = {
  table: ({ children, ...props }) => (
    <div className="overflow-x-auto my-4">
      <table className="w-full border-collapse text-sm" {...props}>
        {children}
      </table>
    </div>
  ),
  thead: ({ children, ...props }) => (
    <thead className="bg-slate-100 dark:bg-slate-800" {...props}>{children}</thead>
  ),
  th: ({ children, ...props }) => (
    <th className="border border-slate-300 dark:border-slate-600 px-3 py-2 text-left font-semibold" {...props}>
      {children}
    </th>
  ),
  td: ({ children, ...props }) => (
    <td className="border border-slate-300 dark:border-slate-600 px-3 py-2" {...props}>
      {children}
    </td>
  ),
  tr: ({ children, ...props }) => (
    <tr className="even:bg-slate-50 dark:even:bg-slate-900/50" {...props}>{children}</tr>
  ),
  h1: ({ children, ...props }) => (
    <h1 className="text-2xl font-bold mt-6 mb-3 text-slate-900 dark:text-slate-100" {...props}>{children}</h1>
  ),
  h2: ({ children, ...props }) => (
    <h2 className="text-xl font-semibold mt-5 mb-2 text-slate-800 dark:text-slate-200" {...props}>{children}</h2>
  ),
  h3: ({ children, ...props }) => (
    <h3 className="text-lg font-semibold mt-4 mb-2 text-slate-800 dark:text-slate-200" {...props}>{children}</h3>
  ),
  h4: ({ children, ...props }) => (
    <h4 className="text-base font-semibold mt-3 mb-1 text-slate-800 dark:text-slate-200" {...props}>{children}</h4>
  ),
  p: ({ children, ...props }) => (
    <p className="my-2 leading-relaxed text-slate-700 dark:text-slate-300" {...props}>{children}</p>
  ),
  ul: ({ children, ...props }) => (
    <ul className="list-disc pl-6 my-2 space-y-1" {...props}>{children}</ul>
  ),
  ol: ({ children, ...props }) => (
    <ol className="list-decimal pl-6 my-2 space-y-1" {...props}>{children}</ol>
  ),
  li: ({ children, ...props }) => (
    <li className="text-slate-700 dark:text-slate-300" {...props}>{children}</li>
  ),
  code: ({ inline, className, children, ...props }: { inline?: boolean; className?: string; children?: React.ReactNode }) => {
    return !inline ? (
      <pre className="bg-slate-900 text-slate-100 rounded-lg p-4 my-3 overflow-x-auto text-sm">
        <code className={className} {...props}>
          {children}
        </code>
      </pre>
    ) : (
      <code className="bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
        {children}
      </code>
    );
  },
  blockquote: ({ children, ...props }) => (
    <blockquote className="border-l-4 border-slate-400 pl-4 my-3 italic text-slate-600 dark:text-slate-400" {...props}>
      {children}
    </blockquote>
  ),
  hr: (props) => (
    <hr className="my-4 border-slate-300 dark:border-slate-600" {...props} />
  ),
  a: ({ children, ...props }) => (
    <a className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 underline" {...props}>
      {children}
    </a>
  ),
  strong: ({ children, ...props }) => (
    <strong className="font-semibold text-slate-900 dark:text-slate-100" {...props}>{children}</strong>
  ),
  em: ({ children, ...props }) => (
    <em className="italic" {...props}>{children}</em>
  ),
};

export const OutputPanel: React.FC<OutputPanelProps> = ({ result, error }) => {
  const processedAnswer = useMemo(() => {
    if (!result?.final_answer) return '';
    return preprocessLLMOutput(result.final_answer);
  }, [result?.final_answer]);

  if (error && !result) {
    return (
      <Card title="Error" className="output-panel error">
        <div className="p-4">
          <p className="text-red-600 dark:text-red-400">{error}</p>
        </div>
      </Card>
    );
  }

  if (!result) {
    return (
      <Card title="Output" className="output-panel empty">
        <div className="p-8 text-center text-slate-500">
          <p>Submit a prompt to see results</p>
        </div>
      </Card>
    );
  }

  if (!result.success) {
    return (
      <Card title="Error" className="output-panel error">
        <div className="p-4 space-y-2">
          <p><strong>Error Type:</strong> {result.error_type || 'Unknown'}</p>
          <p className="text-red-600 dark:text-red-400">{result.error || 'An error occurred'}</p>
          {result.traceback && (
            <details className="mt-4">
              <summary className="cursor-pointer text-sm text-slate-600 dark:text-slate-400">Traceback</summary>
              <pre className="mt-2 bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto text-xs">{result.traceback}</pre>
            </details>
          )}
        </div>
      </Card>
    );
  }

  return (
    <div className="output-panel space-y-4">
      <Card title="Original Prompt" className="output-section">
        <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded">
          <p className="text-slate-700 dark:text-slate-300">{result.original_prompt}</p>
        </div>
      </Card>

      <Card title="Refinement" className="output-section">
        <div className="p-4">
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              result.used_refinement
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                : 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-200'
            }`}
          >
            {result.used_refinement ? 'Refinement Applied' : 'No Refinement'}
          </span>
        </div>
      </Card>

      {result.used_refinement && result.prompt_sent_to_researcher && (
        <Card title="Prompt Sent to Researcher" className="output-section">
          <div className="p-4 bg-slate-50 dark:bg-slate-900/50 rounded">
            <p className="text-slate-700 dark:text-slate-300">{result.prompt_sent_to_researcher}</p>
          </div>
        </Card>
      )}

      <Card title="Final Answer" className="output-section answer">
        <div className="p-4">
          <div className="prose prose-slate dark:prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[[rehypeSanitize, sanitizeSchema], rehypeKatex]}
              components={markdownComponents}
            >
              {processedAnswer}
            </ReactMarkdown>
          </div>
        </div>
      </Card>
    </div>
  );
};
