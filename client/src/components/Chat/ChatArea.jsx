import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from 'framer-motion'
import { useAuth } from '../../context/AuthContext'
import { askStream } from '../../api/chat'
import MessageBubble, { TypingIndicator } from './MessageBubble'

const SUGGESTIONS = [
  { text:'Summarize the key points',       icon:'◈', color:'#00D4FF' },
  { text:'What are the main topics?',       icon:'◈', color:'#8B5CF6' },
  { text:'Find action items or deadlines',  icon:'◈', color:'#00FF88' },
  { text:'Compare across documents',        icon:'◈', color:'#FF0066' },
]

/* ── Orbital Ring ── */
function OrbitalRing({ size, duration, delay=0, reverse=false, color='#00D4FF', dotSize=5 }) {
  return (
    <div style={{
      position:'absolute', width:size, height:size, borderRadius:'50%',
      border:`1px solid ${color}${reverse?'0D':'18'}`,
      animation:`${reverse?'orbitCCW':'orbit'} ${duration}s linear infinite`,
      animationDelay:`${delay}s`,
      boxShadow:`0 0 ${dotSize*3}px ${color}08`,
    }}>
      <div style={{
        position:'absolute', top:-(dotSize/2), left:'50%',
        transform:'translateX(-50%)', width:dotSize, height:dotSize,
        borderRadius:'50%', background:color,
        boxShadow:`0 0 ${dotSize*3}px ${color},0 0 ${dotSize*6}px ${color}55`,
      }}/>
    </div>
  )
}

/* ── Mouse-aware 3D tilt card for suggestions ── */
function TiltCard({ s, i, onSuggest }) {
  const ref    = useRef(null)
  const rotX   = useMotionValue(0)
  const rotY   = useMotionValue(0)
  const glow   = useMotionValue(0)
  const sRotX  = useSpring(rotX,  { stiffness:320, damping:28 })
  const sRotY  = useSpring(rotY,  { stiffness:320, damping:28 })
  const sGlow  = useSpring(glow,  { stiffness:200, damping:22 })
  const glowOpacity = useTransform(sGlow, [0,1], [0, 1])

  const onMove = (e) => {
    const rect = ref.current.getBoundingClientRect()
    const cx = rect.left + rect.width  / 2
    const cy = rect.top  + rect.height / 2
    rotX.set(-(e.clientY - cy) / (rect.height / 2) * 9)
    rotY.set( (e.clientX - cx) / (rect.width  / 2) * 9)
    glow.set(1)
  }
  const onLeave = () => { rotX.set(0); rotY.set(0); glow.set(0) }

  return (
    <motion.div
      initial={{ opacity:0, y:14, scale:.95 }}
      animate={{ opacity:1, y:0,  scale:1 }}
      transition={{ delay: .12*i + .45, ease:[.16,1,.3,1] }}
      style={{ perspective:'700px' }}
    >
      <motion.button
        ref={ref}
        onMouseMove={onMove}
        onMouseLeave={onLeave}
        whileTap={{ scale:.96 }}
        onClick={() => onSuggest(s.text)}
        style={{
          rotateX:sRotX, rotateY:sRotY,
          transformStyle:'preserve-3d',
          width:'100%', textAlign:'left',
          padding:'14px 16px', borderRadius:'16px',
          display:'flex', alignItems:'flex-start', gap:'10px',
          background:`rgba(0,8,20,.65)`,
          border:`1px solid ${s.color}1A`,
          color:'rgba(140,200,230,.6)',
          position:'relative', overflow:'hidden',
          boxShadow:`0 4px 24px rgba(0,0,0,.32),inset 0 1px 0 ${s.color}08`,
          transition:'color .15s,border-color .15s',
        }}
        onMouseEnter={e => {
          e.currentTarget.style.borderColor = `${s.color}38`
          e.currentTarget.style.color = 'rgba(210,240,255,.82)'
          e.currentTarget.style.boxShadow = `0 12px 40px rgba(0,0,0,.45),0 0 30px ${s.color}12,inset 0 1px 0 ${s.color}14`
        }}
        onMouseLeave={e => {
          e.currentTarget.style.borderColor = `${s.color}1A`
          e.currentTarget.style.color = 'rgba(140,200,230,.6)'
          e.currentTarget.style.boxShadow = `0 4px 24px rgba(0,0,0,.32),inset 0 1px 0 ${s.color}08`
        }}
      >
        {/* Hover shimmer layer (depth illusion) */}
        <motion.div style={{
          position:'absolute', inset:0, borderRadius:'inherit',
          background:`linear-gradient(135deg,${s.color}12 0%,transparent 60%)`,
          opacity: glowOpacity,
          pointerEvents:'none',
        }} />
        {/* Icon */}
        <span style={{
          color:s.color, fontSize:'11px', marginTop:'1px', flexShrink:0,
          filter:`drop-shadow(0 0 5px ${s.color})`,
          position:'relative', zIndex:1,
        }}>◈</span>
        <span className="text-xs leading-relaxed" style={{ position:'relative', zIndex:1 }}>{s.text}</span>
      </motion.button>
    </motion.div>
  )
}

/* ── System status chip ── */
function StatusChip({ label, value, color, live = false }) {
  return (
    <div style={{
      display:'flex', flexDirection:'column', gap:2, padding:'7px 13px', borderRadius:10,
      background:`${color}05`, border:`1px solid ${color}12`,
    }}>
      <span className="data-stream" style={{ color:`${color}42`, fontSize:'7px' }}>{label}</span>
      <div style={{ display:'flex', alignItems:'center', gap:5 }}>
        <span style={{ color, fontWeight:700, fontSize:'12px', fontFamily:"'Space Grotesk',sans-serif",
          textShadow:`0 0 12px ${color}45` }}>{value}</span>
        {live && <div style={{ width:3.5, height:3.5, borderRadius:'50%', background:'#00FF88',
          boxShadow:'0 0 5px #00FF88', animation:'breathe 1.6s ease-in-out infinite' }} />}
      </div>
    </div>
  )
}

/* ── Empty state ── */
function EmptyState({ selectedFile, onSuggest }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-5 px-4">
      {/* Orbital visualization */}
      <motion.div
        initial={{ opacity:0, scale:.8 }}
        animate={{ opacity:1, scale:1 }}
        transition={{ duration:.9, ease:[.16,1,.3,1] }}
        style={{ position:'relative', width:252, height:252, display:'flex', alignItems:'center', justifyContent:'center' }}
      >
        <div style={{ position:'absolute', inset:-28, borderRadius:'50%',
          background:'radial-gradient(circle,rgba(0,212,255,.07) 0%,transparent 65%)',
          filter:'blur(20px)', animation:'breathe 5s ease-in-out infinite' }} />
        <OrbitalRing size={240} duration={22} color="#00D4FF" dotSize={5} />
        <OrbitalRing size={184} duration={15} delay={-4} reverse color="#8B5CF6" dotSize={4} />
        <OrbitalRing size={128} duration={10} delay={-2} color="#00FF88" dotSize={3.5} />
        <OrbitalRing size={82}  duration={7}  delay={-1} reverse color="#FF0066" dotSize={3} />
        {/* Center orb */}
        <div style={{ position:'absolute', width:52, height:52, borderRadius:'50%',
          background:'radial-gradient(circle at 38% 32%,rgba(0,212,255,.2) 0%,rgba(139,92,246,.1) 50%,rgba(0,2,10,.95) 100%)',
          boxShadow:'0 0 28px rgba(0,212,255,.22),inset 0 0 18px rgba(0,212,255,.07)',
          animation:'breathe 4s ease-in-out infinite' }} />
        <div className="absolute flex items-baseline" style={{ gap:0 }}>
          <span style={{ fontWeight:900, fontSize:'1.45rem', letterSpacing:'-0.05em', lineHeight:1, color:'#fff',
            textShadow:'0 0 22px rgba(0,212,255,.5)' }}>DOC</span>
          <span className="ai-wordmark" style={{ fontWeight:900, fontSize:'1.45rem', letterSpacing:'-0.05em', lineHeight:1,
            filter:'drop-shadow(0 0 12px rgba(0,212,255,.65))' }}>ai</span>
        </div>
      </motion.div>

      {/* Title */}
      <motion.div initial={{ opacity:0, y:10 }} animate={{ opacity:1, y:0 }} transition={{ delay:.3, duration:.5 }}
        className="text-center" style={{ marginTop:-6 }}>
        <p style={{ fontSize:'15px', fontWeight:600, color:'rgba(190,230,255,.7)', letterSpacing:'-0.02em', marginBottom:5 }}>
          Transform documents into intelligence.
        </p>
        <div style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:8 }}>
          <div style={{ width:36, height:1, background:'linear-gradient(90deg,transparent,rgba(0,212,255,.2))' }} />
          <span className="data-stream" style={{ color:'rgba(0,212,255,.28)', fontSize:'7.5px' }}>
            {selectedFile ? `FOCUSED · ${selectedFile.toUpperCase().slice(0,22)}` : 'ALL DOCUMENTS · READY'}
          </span>
          <div style={{ width:36, height:1, background:'linear-gradient(90deg,rgba(0,212,255,.2),transparent)' }} />
        </div>
      </motion.div>

      {/* Live system metrics */}
      <motion.div initial={{ opacity:0, y:8 }} animate={{ opacity:1, y:0 }} transition={{ delay:.48, duration:.4 }}
        style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:6, width:'100%', maxWidth:480 }}>
        <StatusChip label="VECTORS"  value="14.2K"  color="#00D4FF" live />
        <StatusChip label="ACCURACY" value="99.7%"  color="#00FF88" />
        <StatusChip label="MODELS"   value="2 / 2"  color="#8B5CF6" live />
        <StatusChip label="LATENCY"  value="142ms"  color="#FF4466" />
      </motion.div>

      {/* Suggestion cards */}
      <div className="grid grid-cols-2 gap-2.5 max-w-lg w-full">
        {SUGGESTIONS.map((s, i) => <TiltCard key={s.text} s={s} i={i} onSuggest={onSuggest} />)}
      </div>
    </div>
  )
}

/* ── Magnetic send button ── */
function MagneticSendBtn({ onClick, disabled, loading, active }) {
  const ref   = useRef(null)
  const mx    = useMotionValue(0)
  const my    = useMotionValue(0)
  const smx   = useSpring(mx, { stiffness:340, damping:22 })
  const smy   = useSpring(my, { stiffness:340, damping:22 })

  const onMove = (e) => {
    if (disabled) return
    const rect = ref.current.getBoundingClientRect()
    mx.set((e.clientX - (rect.left + rect.width  / 2)) * .38)
    my.set((e.clientY - (rect.top  + rect.height / 2)) * .38)
  }
  const onLeave = () => { mx.set(0); my.set(0) }

  return (
    <motion.button
      ref={ref}
      style={{ x:smx, y:smy }}
      whileTap={active ? { scale:.88 } : {}}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      onClick={onClick}
      disabled={disabled}
      className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center"
      style2={{ transition:'background .2s,box-shadow .2s' }}
    >
      <div style={{
        width:36, height:36, borderRadius:12,
        display:'flex', alignItems:'center', justifyContent:'center',
        background: active
          ? 'linear-gradient(135deg,#0099CC,#00D4FF,#8B5CF6)'
          : 'rgba(0,212,255,.04)',
        boxShadow: active
          ? '0 0 28px rgba(0,212,255,.5),0 4px 14px rgba(0,0,0,.35)'
          : '0 2px 8px rgba(0,0,0,.2)',
        border: active ? 'none' : '1px solid rgba(0,212,255,.07)',
        transition:'all .2s ease',
        cursor: active ? 'pointer' : 'not-allowed',
      }}>
        {loading ? (
          <div className="w-4 h-4 border-2 border-white/15 border-t-white/55 rounded-full animate-spin" />
        ) : (
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        )}
      </div>
    </motion.button>
  )
}

export default function ChatArea({ messages, setMessages, conversationId, setConversationId, selectedFile }) {
  const { token }  = useAuth()
  const [input, setInput]         = useState('')
  const [loading, setLoading]     = useState(false)
  const [streaming, setStreaming] = useState('')
  const [focused, setFocused]     = useState(false)
  const bottomRef  = useRef(null)
  const textRef    = useRef(null)
  const isStreaming = loading && streaming !== ''

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior:'smooth' }) }, [messages, streaming])

  const handleSubmit = async (q) => {
    const query = (q || input).trim()
    if (!query || loading) return
    setInput(''); setLoading(true); setStreaming('')
    const userMsg = { role:'user', content:query }
    const history = [...messages, userMsg]
    setMessages(history)
    try {
      await askStream({
        query, chatHistory:history, conversationId, selectedFile, token,
        onChunk:(t) => setStreaming(t),
        onDone:(t) => { setMessages(p => [...p,{ role:'assistant', content:t }]); setStreaming('') },
        onConversationId:(id) => setConversationId(id),
      })
    } catch(e) {
      setMessages(p => [...p,{ role:'assistant', content:`Error: ${e.message}` }]); setStreaming('')
    } finally { setLoading(false) }
  }

  const onKey = (e) => { if(e.key==='Enter'&&!e.shiftKey){ e.preventDefault(); handleSubmit() } }
  const resize = () => {
    const el = textRef.current; if(!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight,150)+'px'
  }

  const containerStyle = {
    background: focused ? 'rgba(0,15,35,.92)' : 'rgba(0,8,22,.72)',
    border: focused ? '1px solid rgba(0,212,255,.42)' : '1px solid rgba(0,212,255,.1)',
    boxShadow: focused
      ? '0 0 0 1px rgba(0,212,255,.1),0 0 55px rgba(0,212,255,.08),inset 0 1px 0 rgba(0,212,255,.07),0 8px 40px rgba(0,0,0,.55)'
      : '0 4px 32px rgba(0,0,0,.38),inset 0 1px 0 rgba(0,212,255,.03)',
    transition:'all .28s ease',
  }

  return (
    <div className="flex flex-col h-full">

      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3.5 border-b flex-shrink-0"
        style={{ borderColor:'rgba(0,212,255,.06)', background:'rgba(0,3,10,.92)',
          backdropFilter:'blur(24px)', boxShadow:'0 1px 0 rgba(0,212,255,.04)' }}>
        <div className="flex items-center gap-3">
          <div className="flex items-baseline gap-0">
            <span style={{ fontWeight:900, fontSize:'1.02rem', letterSpacing:'-0.04em', color:'#fff' }}>DOC</span>
            <span className="ai-wordmark" style={{ fontWeight:900, fontSize:'1.02rem', letterSpacing:'-0.04em' }}>ai</span>
          </div>
          <AnimatePresence>
            {selectedFile && (
              <motion.span
                initial={{ opacity:0, scale:.88, x:-6 }}
                animate={{ opacity:1, scale:1, x:0 }}
                exit={{ opacity:0, scale:.88, x:-6 }}
                className="px-2.5 py-1 rounded-lg text-xs flex items-center gap-1.5"
                style={{ background:'rgba(0,212,255,.06)', color:'rgba(0,212,255,.7)',
                  border:'1px solid rgba(0,212,255,.14)', boxShadow:'0 0 14px rgba(0,212,255,.06)' }}
              >
                <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
                </svg>
                {selectedFile}
              </motion.span>
            )}
          </AnimatePresence>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full status-online animate-pulse-glow" />
          <span className="data-stream" style={{ color:'rgba(0,212,255,.3)' }}>
            {selectedFile?'SINGLE DOCUMENT':'ALL DOCUMENTS'}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length===0&&!loading ? (
          <EmptyState selectedFile={selectedFile} onSuggest={handleSubmit} />
        ) : (
          <div>
            {messages.map((m,i)=>(<MessageBubble key={i} role={m.role} content={m.content} />))}
            <AnimatePresence>
              {loading&&!isStreaming&&<TypingIndicator/>}
            </AnimatePresence>
            {isStreaming&&<MessageBubble role="assistant" content={streaming} isStreaming/>}
            <div ref={bottomRef}/>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="px-6 py-4 flex-shrink-0">
        <div className="relative flex items-end gap-3 p-3.5 rounded-2xl" style={containerStyle}>
          {/* Focus pulse ring */}
          <AnimatePresence>
            {focused && (
              <motion.div
                initial={{ opacity:0, scale:.97 }}
                animate={{ opacity:1, scale:1 }}
                exit={{ opacity:0 }}
                style={{
                  position:'absolute', inset:-2, borderRadius:'18px',
                  border:'1px solid rgba(0,212,255,.14)',
                  pointerEvents:'none',
                  boxShadow:'0 0 0 5px rgba(0,212,255,.03)',
                }}
              />
            )}
          </AnimatePresence>

          <textarea
            ref={textRef}
            value={input}
            onChange={e=>{setInput(e.target.value);resize()}}
            onKeyDown={onKey}
            onFocus={()=>setFocused(true)}
            onBlur={()=>setFocused(false)}
            placeholder="Ask about your documents…"
            rows={1}
            disabled={loading}
            className="flex-1 bg-transparent resize-none outline-none text-sm leading-relaxed py-1"
            style={{ color:'rgba(210,240,255,.9)', maxHeight:'150px', overflowY:'auto',
              letterSpacing:'-0.01em', caretColor:'#00D4FF' }}
          />

          <MagneticSendBtn
            onClick={handleSubmit}
            disabled={!input.trim()||loading}
            loading={loading}
            active={!!input.trim()&&!loading}
          />
        </div>
        <p className="text-center text-xs mt-2 data-stream" style={{ color:'rgba(0,212,255,.14)' }}>
          ENTER TO SEND · SHIFT+ENTER FOR NEW LINE
        </p>
      </div>
    </div>
  )
}
