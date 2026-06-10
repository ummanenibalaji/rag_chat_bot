import { useRef } from 'react'
import { motion, useMotionValue, useSpring } from 'framer-motion'
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
        borderRadius: '12px', fontSize: '12.5px', margin: '10px 0',
        border: '1px solid rgba(0,212,255,0.1)', background: 'rgba(0,4,12,0.8)',
        boxShadow: 'inset 0 1px 0 rgba(0,212,255,0.05), 0 4px 20px rgba(0,0,0,0.5)',
      }}
    >
      {String(children).replace(/\n$/, '')}
    </SyntaxHighlighter>
  )
}

function UserAvatar() {
  return (
    <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
      style={{
        background:'linear-gradient(135deg,rgba(0,153,204,.85),rgba(0,212,255,.7),rgba(139,92,246,.6))',
        boxShadow:'0 0 16px rgba(0,212,255,.35),inset 0 1px 0 rgba(255,255,255,.1)',
      }}>
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
      </svg>
    </div>
  )
}

function AIAvatar() {
  return (
    <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 holo-shimmer"
      style={{
        background:'rgba(0,212,255,.06)', border:'1px solid rgba(0,212,255,.18)',
        boxShadow:'0 0 12px rgba(0,212,255,.12),inset 0 1px 0 rgba(0,212,255,.08)',
      }}>
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <defs>
          <linearGradient id="ai-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#00D4FF"/>
            <stop offset="50%" stopColor="#8B5CF6"/>
            <stop offset="100%" stopColor="#00D4FF"/>
          </linearGradient>
        </defs>
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="url(#ai-grad)"/>
      </svg>
    </div>
  )
}

/* ── 3D tilt bubble wrapper ── */
function TiltBubble({ isUser, children, style }) {
  const ref   = useRef(null)
  const rotX  = useMotionValue(0)
  const rotY  = useMotionValue(0)
  const glow  = useMotionValue(0)
  const sRotX = useSpring(rotX, { stiffness:280, damping:26 })
  const sRotY = useSpring(rotY, { stiffness:280, damping:26 })
  const sGlow = useSpring(glow, { stiffness:200, damping:22 })

  const onMove = (e) => {
    const rect = ref.current.getBoundingClientRect()
    const cx = rect.left + rect.width  / 2
    const cy = rect.top  + rect.height / 2
    rotX.set(-(e.clientY - cy) / (rect.height / 2) * 4)
    rotY.set( (e.clientX - cx) / (rect.width  / 2) * 4)
    glow.set(1)
  }
  const onLeave = () => { rotX.set(0); rotY.set(0); glow.set(0) }

  return (
    <motion.div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      style={{
        rotateX: sRotX, rotateY: sRotY,
        transformStyle:'preserve-3d',
        maxWidth:'76%',
        ...style,
      }}
    >
      {/* Glow intensification layer */}
      <motion.div
        style={{
          position:'absolute', inset:0, borderRadius:'inherit', pointerEvents:'none',
          boxShadow: isUser
            ? `0 0 40px rgba(0,212,255,${0.22 * (sGlow.get?.() ?? 0)})`
            : `0 0 40px rgba(0,212,255,${0.15 * (sGlow.get?.() ?? 0)})`,
          opacity: sGlow,
          background: isUser
            ? 'radial-gradient(ellipse at center,rgba(0,212,255,.04) 0%,transparent 70%)'
            : 'radial-gradient(ellipse at center,rgba(0,212,255,.03) 0%,transparent 70%)',
          zIndex:0,
        }}
      />
      <div style={{ position:'relative', zIndex:1 }}>
        {children}
      </div>
    </motion.div>
  )
}

export default function MessageBubble({ role, content, isStreaming = false }) {
  const isUser = role === 'user'

  return (
    <motion.div
      initial={{ opacity:0, y:14, scale:.97 }}
      animate={{ opacity:1, y:0,  scale:1 }}
      transition={{ duration:.28, ease:[.16,1,.3,1] }}
      className={`flex gap-3 ${isUser?'flex-row-reverse':'flex-row'} mb-5`}
      style={{ perspective:'900px' }}
    >
      {isUser ? <UserAvatar /> : <AIAvatar />}

      <TiltBubble isUser={isUser}>
        <div
          className={`${isUser?'message-user':'message-ai'} px-4 py-3`}
          style={!isUser ? {
            boxShadow:'0 4px 24px rgba(0,0,0,.35),inset 0 1px 0 rgba(0,212,255,.05)',
          } : {
            boxShadow:'0 4px 24px rgba(0,0,0,.3),0 0 20px rgba(0,212,255,.04)',
          }}
        >
          {isUser ? (
            <p className="text-sm leading-relaxed" style={{ color:'rgba(210,240,255,.9)', letterSpacing:'-0.01em' }}>
              {content}
            </p>
          ) : (
            <div className="text-sm leading-relaxed">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  table:({ children }) => (
                    <div className="overflow-x-auto my-3 rounded-xl" style={{ border:'1px solid rgba(0,212,255,.08)' }}>
                      <table className="w-full text-sm border-collapse">{children}</table>
                    </div>
                  ),
                  thead:({ children }) => (
                    <thead style={{ background:'rgba(0,212,255,.05)', borderBottom:'1px solid rgba(0,212,255,.12)' }}>{children}</thead>
                  ),
                  tbody:({ children }) => <tbody>{children}</tbody>,
                  tr:({ children }) => (
                    <tr style={{ borderBottom:'1px solid rgba(0,212,255,.04)', transition:'background .12s' }}
                      onMouseEnter={e => e.currentTarget.style.background='rgba(0,212,255,.02)'}
                      onMouseLeave={e => e.currentTarget.style.background='transparent'}
                    >{children}</tr>
                  ),
                  th:({ children }) => (
                    <th className="px-3 py-2.5 text-left font-semibold text-xs"
                      style={{ color:'rgba(0,212,255,.7)', letterSpacing:'.04em', fontFamily:"'Space Grotesk',sans-serif" }}>
                      {children}
                    </th>
                  ),
                  td:({ children }) => (
                    <td className="px-3 py-2" style={{ color:'rgba(140,200,230,.55)', fontSize:'12.5px' }}>{children}</td>
                  ),
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className||'')
                    return !inline && match ? (
                      <CodeBlock language={match[1]}>{children}</CodeBlock>
                    ) : (
                      <code className="px-1.5 py-0.5 rounded text-xs font-mono"
                        style={{ background:'rgba(0,212,255,.07)', color:'rgba(0,212,255,.8)', border:'1px solid rgba(0,212,255,.14)' }}
                        {...props}
                      >{children}</code>
                    )
                  },
                  p:({ children }) => (
                    <p className="mb-2 last:mb-0" style={{ color:'rgba(170,215,240,.8)', letterSpacing:'-0.01em', lineHeight:'1.7' }}>{children}</p>
                  ),
                  ul:({ children }) => <ul className="pl-4 mb-2 space-y-1.5" style={{ listStyleType:'none' }}>{children}</ul>,
                  ol:({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-1.5" style={{ color:'rgba(140,200,230,.65)' }}>{children}</ol>,
                  li:({ children }) => (
                    <li className="text-sm flex items-start gap-2" style={{ color:'rgba(140,200,230,.65)' }}>
                      <span style={{ color:'#00D4FF', fontSize:'10px', marginTop:'5px', flexShrink:0, filter:'drop-shadow(0 0 4px #00D4FF)' }}>◈</span>
                      <span>{children}</span>
                    </li>
                  ),
                  strong:({ children }) => <strong style={{ color:'rgba(210,240,255,.9)', fontWeight:600 }}>{children}</strong>,
                  em:({ children }) => <em style={{ color:'rgba(140,200,230,.7)', fontStyle:'italic' }}>{children}</em>,
                  h1:({ children }) => (
                    <h1 className="font-bold text-base mb-2 mt-4 first:mt-0"
                      style={{ color:'rgba(210,240,255,.95)', letterSpacing:'-0.03em', textShadow:'0 0 20px rgba(0,212,255,.2)' }}>
                      {children}
                    </h1>
                  ),
                  h2:({ children }) => (
                    <h2 className="font-semibold text-sm mb-2 mt-4 first:mt-0" style={{ color:'rgba(200,235,255,.88)', letterSpacing:'-0.02em' }}>{children}</h2>
                  ),
                  h3:({ children }) => (
                    <h3 className="font-semibold text-sm mb-1.5 mt-3 first:mt-0" style={{ color:'rgba(180,225,255,.8)', letterSpacing:'-0.01em' }}>{children}</h3>
                  ),
                  blockquote:({ children }) => (
                    <blockquote className="pl-3 my-3 py-1"
                      style={{ borderLeft:'2px solid rgba(0,212,255,.35)', color:'rgba(140,200,230,.5)', fontStyle:'italic',
                        background:'rgba(0,212,255,.02)', borderRadius:'0 8px 8px 0' }}>
                      {children}
                    </blockquote>
                  ),
                  hr:() => <hr style={{ border:'none', borderTop:'1px solid rgba(0,212,255,.08)', margin:'16px 0' }} />,
                }}
              >
                {content}
              </ReactMarkdown>
              {isStreaming && (
                <span className="inline-block w-1.5 h-4 ml-0.5 rounded-sm"
                  style={{
                    background:'linear-gradient(135deg,#00D4FF,#8B5CF6)',
                    animation:'breathe .7s ease-in-out infinite',
                    boxShadow:'0 0 8px rgba(0,212,255,.5)',
                  }} />
              )}
            </div>
          )}
        </div>
      </TiltBubble>
    </motion.div>
  )
}

export function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity:0, y:10 }} animate={{ opacity:1, y:0 }} exit={{ opacity:0, y:10 }}
      className="flex gap-3 mb-5"
    >
      <AIAvatar />
      <div className="message-ai px-4 py-3.5 flex items-center gap-1.5"
        style={{ boxShadow:'0 4px 24px rgba(0,0,0,.35)' }}>
        <div className="typing-dot" />
        <div className="typing-dot" />
        <div className="typing-dot" />
      </div>
    </motion.div>
  )
}
