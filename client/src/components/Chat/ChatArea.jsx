import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../../context/AuthContext'
import { askStream } from '../../api/chat'
import MessageBubble, { TypingIndicator } from './MessageBubble'

const SUGGESTIONS = [
  'Summarize the key points of my documents',
  'What are the main topics covered?',
  'Find any action items or deadlines',
  'Compare information across documents',
]

export default function ChatArea({ messages, setMessages, conversationId, setConversationId, selectedFile }) {
  const { token } = useAuth()
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)
  const isStreaming = loading && streamingContent !== ''

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const handleSubmit = async (query) => {
    const q = (query || input).trim()
    if (!q || loading) return

    setInput('')
    setLoading(true)
    setStreamingContent('')

    const userMsg = { role: 'user', content: q }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)

    try {
      let full = ''
      await askStream({
        query: q,
        chatHistory: newMessages,
        conversationId,
        selectedFile,
        token,
        onChunk: (text) => {
          full = text
          setStreamingContent(text)
        },
        onDone: (text) => {
          setMessages(prev => [...prev, { role: 'assistant', content: text }])
          setStreamingContent('')
        },
        onConversationId: (id) => setConversationId(id),
      })
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}` }])
      setStreamingContent('')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const adjustHeight = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 150) + 'px'
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header bar */}
      <div className="flex items-center justify-between px-6 py-3 border-b flex-shrink-0"
        style={{ borderColor: 'rgba(255,255,255,0.06)', background: 'rgba(6,11,24,0.8)', backdropFilter: 'blur(12px)' }}>
        <div className="flex items-center gap-3">
          <h1 className="font-semibold text-sm" style={{ color: '#E2E8F0' }}>AI Document Chat</h1>
          {selectedFile && (
            <span className="px-2 py-0.5 rounded-full text-xs" style={{ background: 'rgba(99,102,241,0.15)', color: '#818CF8', border: '1px solid rgba(99,102,241,0.2)' }}>
              📄 {selectedFile}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ background: '#10B981', boxShadow: '0 0 6px rgba(16,185,129,0.6)' }} />
          <span className="text-xs" style={{ color: '#475569' }}>
            {selectedFile ? 'Single file mode' : 'All documents'}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && !loading ? (
          <div className="flex flex-col items-center justify-center h-full gap-6">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4 }}
              className="text-center"
            >
              <div className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center"
                style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.15))', border: '1px solid rgba(99,102,241,0.2)' }}>
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="#818CF8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h2 className="text-xl font-semibold mb-2 text-gradient">What would you like to know?</h2>
              <p className="text-sm" style={{ color: '#475569' }}>
                Ask anything about your uploaded documents
              </p>
            </motion.div>

            {/* Suggestions */}
            <div className="grid grid-cols-2 gap-2 max-w-lg w-full">
              {SUGGESTIONS.map((s, i) => (
                <motion.button
                  key={s}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 + 0.2 }}
                  onClick={() => handleSubmit(s)}
                  className="text-left p-3 rounded-xl text-xs transition-all duration-200"
                  style={{
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.07)',
                    color: '#94A3B8',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.background = 'rgba(99,102,241,0.08)'
                    e.currentTarget.style.borderColor = 'rgba(99,102,241,0.2)'
                    e.currentTarget.style.color = '#C7D2FE'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.03)'
                    e.currentTarget.style.borderColor = 'rgba(255,255,255,0.07)'
                    e.currentTarget.style.color = '#94A3B8'
                  }}
                >
                  {s}
                </motion.button>
              ))}
            </div>
          </div>
        ) : (
          <div>
            {messages.map((msg, i) => (
              <MessageBubble key={i} role={msg.role} content={msg.content} />
            ))}
            <AnimatePresence>
              {loading && !isStreaming && <TypingIndicator />}
            </AnimatePresence>
            {isStreaming && (
              <MessageBubble role="assistant" content={streamingContent} isStreaming />
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="px-6 py-4 flex-shrink-0">
        <div className="relative flex items-end gap-3 p-3 rounded-2xl transition-all duration-200"
          style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.1)',
            boxShadow: '0 4px 24px rgba(0,0,0,0.2)',
          }}
          onFocus={() => {}}
        >
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => { setInput(e.target.value); adjustHeight() }}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your documents..."
            rows={1}
            className="flex-1 bg-transparent resize-none outline-none text-sm leading-relaxed py-1"
            style={{ color: '#E2E8F0', maxHeight: '150px', overflowY: 'auto' }}
            disabled={loading}
          />
          <button
            onClick={() => handleSubmit()}
            disabled={!input.trim() || loading}
            className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200"
            style={input.trim() && !loading
              ? { background: 'linear-gradient(135deg, #6366F1, #8B5CF6)', boxShadow: '0 0 12px rgba(99,102,241,0.4)' }
              : { background: 'rgba(255,255,255,0.05)', cursor: 'not-allowed' }
            }
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            )}
          </button>
        </div>
        <p className="text-center text-xs mt-2" style={{ color: '#1E293B' }}>
          Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
