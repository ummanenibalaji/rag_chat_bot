import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

function CodeBlock({ language, children }) {
  return (
    <SyntaxHighlighter
      style={oneDark}
      language={language || 'text'}
      PreTag="div"
      customStyle={{
        borderRadius: '10px',
        fontSize: '13px',
        margin: '8px 0',
        border: '1px solid rgba(255,255,255,0.08)',
      }}
    >
      {String(children).replace(/\n$/, '')}
    </SyntaxHighlighter>
  )
}

export default function MessageBubble({ role, content, isStreaming = false }) {
  const isUser = role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'} mb-4`}
    >
      {/* Avatar */}
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 mt-0.5"
        style={isUser
          ? { background: 'linear-gradient(135deg, #6366F1, #8B5CF6)' }
          : { background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.1)' }
        }
      >
        {isUser ? '👤' : '🧠'}
      </div>

      {/* Bubble */}
      <div className={`max-w-[75%] ${isUser ? 'message-user' : 'message-ai'} px-4 py-3`}>
        {isUser ? (
          <p className="text-sm leading-relaxed" style={{ color: '#E2E8F0' }}>{content}</p>
        ) : (
          <div className="text-sm leading-relaxed prose-ai">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({ children }) => (
                  <div className="overflow-x-auto my-3">
                    <table className="w-full text-sm border-collapse" style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
                      {children}
                    </table>
                  </div>
                ),
                thead: ({ children }) => (
                  <thead style={{ background: 'rgba(99,102,241,0.15)' }}>{children}</thead>
                ),
                tbody: ({ children }) => <tbody>{children}</tbody>,
                tr: ({ children }) => (
                  <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>{children}</tr>
                ),
                th: ({ children }) => (
                  <th className="px-3 py-2 text-left font-semibold" style={{ color: '#A5B4FC', borderBottom: '1px solid rgba(99,102,241,0.3)' }}>
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="px-3 py-2" style={{ color: '#CBD5E1' }}>{children}</td>
                ),
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '')
                  return !inline && match ? (
                    <CodeBlock language={match[1]}>{children}</CodeBlock>
                  ) : (
                    <code
                      className="px-1.5 py-0.5 rounded text-xs font-mono"
                      style={{ background: 'rgba(99,102,241,0.15)', color: '#A5B4FC', border: '1px solid rgba(99,102,241,0.2)' }}
                      {...props}
                    >
                      {children}
                    </code>
                  )
                },
                p: ({ children }) => <p className="mb-2 last:mb-0" style={{ color: '#CBD5E1' }}>{children}</p>,
                ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-1" style={{ color: '#CBD5E1' }}>{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-1" style={{ color: '#CBD5E1' }}>{children}</ol>,
                li: ({ children }) => <li className="text-sm">{children}</li>,
                strong: ({ children }) => <strong style={{ color: '#E2E8F0' }}>{children}</strong>,
                h3: ({ children }) => <h3 className="font-semibold text-sm mb-1 mt-3" style={{ color: '#E2E8F0' }}>{children}</h3>,
                blockquote: ({ children }) => (
                  <blockquote className="pl-3 my-2" style={{ borderLeft: '3px solid rgba(99,102,241,0.5)', color: '#94A3B8' }}>{children}</blockquote>
                ),
              }}
            >
              {content}
            </ReactMarkdown>
            {isStreaming && (
              <span className="inline-block w-1.5 h-4 ml-0.5 rounded-sm animate-pulse" style={{ background: '#6366F1' }} />
            )}
          </div>
        )}
      </div>
    </motion.div>
  )
}

export function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      className="flex gap-3 mb-4"
    >
      <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0"
        style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.1)' }}>
        🧠
      </div>
      <div className="message-ai px-4 py-3 flex items-center gap-1.5">
        <div className="typing-dot" />
        <div className="typing-dot" />
        <div className="typing-dot" />
      </div>
    </motion.div>
  )
}
