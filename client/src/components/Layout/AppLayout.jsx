import { useState, useEffect, useRef, useCallback } from 'react'
import { useMotionValue, useSpring, useTransform, motion } from 'framer-motion'
import Sidebar from './Sidebar'
import ChatArea from '../Chat/ChatArea'

/* ─── Neural particle canvas (mouse-repel) ─── */
function ParticleCanvas() {
  const canvasRef = useRef(null)
  const mouse     = useRef({ x: -1000, y: -1000 })

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx    = canvas.getContext('2d')
    let animId, particles

    const resize = () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; init() }
    const onMove = (e) => { mouse.current = { x: e.clientX, y: e.clientY } }

    function init() {
      const count = Math.min(Math.floor((canvas.width * canvas.height) / 17000), 95)
      particles = Array.from({ length: count }, () => ({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - .5) * .38,
        vy: (Math.random() - .5) * .38,
        r: Math.random() * 1.8 + .4,
        hue: Math.random() < .6 ? 188 + Math.random() * 22 : 270 + Math.random() * 28,
        ph: Math.random() * Math.PI * 2,
      }))
    }

    let t = 0
    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      t += .004
      const mx = mouse.current.x, my = mouse.current.y

      particles.forEach((p, i) => {
        // Mouse repulsion
        const dx = p.x - mx, dy = p.y - my
        const d  = Math.sqrt(dx * dx + dy * dy)
        if (d < 100) {
          const f = (100 - d) / 100 * .012
          p.vx += (dx / d) * f
          p.vy += (dy / d) * f
        }
        // Speed cap
        const spd = Math.sqrt(p.vx * p.vx + p.vy * p.vy)
        if (spd > .7) { p.vx *= .97; p.vy *= .97 }

        p.x += p.vx; p.y += p.vy
        if (p.x < 0) p.x = canvas.width
        if (p.x > canvas.width) p.x = 0
        if (p.y < 0) p.y = canvas.height
        if (p.y > canvas.height) p.y = 0

        const pulse = .62 + .38 * Math.sin(t * 1.7 + p.ph)

        // Connections
        for (let j = i + 1; j < particles.length; j++) {
          const q = particles[j]
          const ex = p.x - q.x, ey = p.y - q.y
          const ed = Math.sqrt(ex * ex + ey * ey)
          if (ed < 135) {
            const alpha = (1 - ed / 135) * .07 * pulse
            const g = ctx.createLinearGradient(p.x, p.y, q.x, q.y)
            g.addColorStop(0, `hsla(${p.hue},100%,65%,${alpha})`)
            g.addColorStop(1, `hsla(${q.hue},100%,65%,${alpha})`)
            ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y)
            ctx.strokeStyle = g; ctx.lineWidth = .6; ctx.stroke()
          }
        }

        // Core
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
        ctx.fillStyle = `hsla(${p.hue},100%,72%,${.2 * pulse + .08})`; ctx.fill()
        if (p.r > 1.2) {
          ctx.beginPath(); ctx.arc(p.x, p.y, p.r * 4.5, 0, Math.PI * 2)
          ctx.fillStyle = `hsla(${p.hue},100%,72%,${.06 * pulse})`; ctx.fill()
        }
      })
      animId = requestAnimationFrame(draw)
    }

    resize(); draw()
    window.addEventListener('resize', resize)
    window.addEventListener('mousemove', onMove)
    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', resize)
      window.removeEventListener('mousemove', onMove)
    }
  }, [])

  return (
    <canvas ref={canvasRef} style={{ position:'fixed', inset:0, pointerEvents:'none', zIndex:0, opacity:.65 }} />
  )
}

/* ─── Scan beam ─── */
function ScanBeam() {
  return (
    <div style={{
      position:'fixed', left:0, right:0, height:'1.5px',
      background:'linear-gradient(90deg,transparent,rgba(0,212,255,.18),rgba(139,92,246,.12),transparent)',
      pointerEvents:'none', zIndex:2, animation:'scanMove 14s linear infinite',
      boxShadow:'0 0 12px rgba(0,212,255,.22)',
    }} />
  )
}

/* ─── Enhanced HUD Corner accents ─── */
function CornerAccent({ pos }) {
  const s = {
    tl:{ top:0,    left:0 },
    tr:{ top:0,    right:0,  transform:'scaleX(-1)' },
    bl:{ bottom:0, left:0,   transform:'scaleY(-1)' },
    br:{ bottom:0, right:0,  transform:'scale(-1)' },
  }
  return (
    <div style={{ position:'fixed', width:60, height:60, pointerEvents:'none', zIndex:3, ...s[pos] }}>
      <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
        <path d="M2 34 L2 2 L34 2" stroke="rgba(0,212,255,.45)" strokeWidth="1.5" strokeLinecap="round"/>
        <path d="M2 22 L2 2 L22 2" stroke="rgba(0,212,255,.18)" strokeWidth=".8" strokeLinecap="round"/>
        <circle cx="2" cy="2" r="2.5" fill="rgba(0,212,255,.4)" />
      </svg>
    </div>
  )
}

/* ─── HUD Status Bar ─── */
function HudStatusBar() {
  const [time, setTime] = useState('')
  useEffect(() => {
    const fmt = () => {
      const n = new Date()
      setTime(n.toLocaleTimeString('en-US', { hour12:false, hour:'2-digit', minute:'2-digit', second:'2-digit' }))
    }
    fmt()
    const id = setInterval(fmt, 1000)
    return () => clearInterval(id)
  }, [])

  const metrics = [
    { label:'HYBRID RETRIEVAL', val:'ACTIVE',  color:'#00FF88' },
    { label:'FAISS INDEX',      val:'ONLINE',  color:'#00D4FF' },
    { label:'CROSS-ENCODER',    val:'READY',   color:'#8B5CF6' },
    { label:'MODEL',            val:'LLAMA3',  color:'#00D4FF' },
  ]

  return (
    <div style={{
      flexShrink:0, height:26, zIndex:5,
      background:'rgba(0,2,10,.94)',
      borderTop:'1px solid rgba(0,212,255,.07)',
      display:'flex', alignItems:'center', justifyContent:'space-between',
      padding:'0 16px', gap:8,
      backdropFilter:'blur(20px)',
    }}>
      {/* Left: status dots */}
      <div style={{ display:'flex', alignItems:'center', gap:14 }}>
        {metrics.map(m => (
          <div key={m.label} style={{ display:'flex', alignItems:'center', gap:5 }}>
            <div style={{ width:4, height:4, borderRadius:'50%', background:m.color,
              boxShadow:`0 0 5px ${m.color}`, animation:'breathe 3s ease-in-out infinite' }} />
            <span className="data-stream" style={{ color:'rgba(0,212,255,.22)', fontSize:'7px' }}>{m.label}</span>
            <span className="data-stream" style={{ color:`${m.color}55`, fontSize:'7px' }}>{m.val}</span>
          </div>
        ))}
      </div>
      {/* Center: brand */}
      <div style={{ display:'flex', alignItems:'center', gap:5, position:'absolute', left:'50%', transform:'translateX(-50%)' }}>
        <div style={{ width:1, height:8, background:'rgba(0,212,255,.2)' }} />
        <span className="data-stream" style={{ color:'rgba(0,212,255,.18)', letterSpacing:'.18em', fontSize:'7px' }}>DOCai NEURAL SYSTEM</span>
        <div style={{ width:1, height:8, background:'rgba(0,212,255,.2)' }} />
      </div>
      {/* Right: clock */}
      <div style={{ display:'flex', alignItems:'center', gap:8 }}>
        <span className="data-stream" style={{ color:'rgba(0,212,255,.35)', fontSize:'7.5px', fontVariantNumeric:'tabular-nums',
          letterSpacing:'.1em' }}>{time}</span>
        <div style={{ display:'flex', alignItems:'center', gap:4 }}>
          <div style={{ width:5, height:5, borderRadius:'50%', background:'#00FF88',
            boxShadow:'0 0 6px #00FF88', animation:'breathe 2s ease-in-out infinite' }} />
          <span className="data-stream" style={{ color:'rgba(0,255,136,.4)', fontSize:'7px' }}>SYS ONLINE</span>
        </div>
      </div>
    </div>
  )
}

export default function AppLayout() {
  const [messages, setMessages]         = useState([])
  const [conversationId, setConversationId] = useState(null)
  const [activeConvId, setActiveConvId] = useState(null)
  const [selectedFile, setSelectedFile] = useState(null)

  /* ── Mouse parallax for orbs ── */
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)
  const spX = useSpring(mouseX, { stiffness: 38, damping: 22 })
  const spY = useSpring(mouseY, { stiffness: 38, damping: 22 })
  const orb1x = useTransform(spX, v => v * .55)
  const orb1y = useTransform(spY, v => v * .55)
  const orb2x = useTransform(spX, v => v * -.4)
  const orb2y = useTransform(spY, v => v * -.4)
  const orb3x = useTransform(spX, v => v * .28)
  const orb3y = useTransform(spY, v => v * .28)

  useEffect(() => {
    const h = (e) => {
      mouseX.set((e.clientX / window.innerWidth  - .5) * 50)
      mouseY.set((e.clientY / window.innerHeight - .5) * 50)
    }
    window.addEventListener('mousemove', h)
    return () => window.removeEventListener('mousemove', h)
  }, [])

  const handleConversationSelect = (id, msgs) => { setActiveConvId(id); setConversationId(id); setMessages(msgs) }
  const handleNewChat = () => { setMessages([]); setConversationId(null); setActiveConvId(null) }

  return (
    <div className="flex flex-col h-screen overflow-hidden mesh-bg" style={{ position:'relative' }}>

      {/* Circuit grid */}
      <div className="circuit-grid absolute inset-0 pointer-events-none" style={{ zIndex:0 }} />
      <ParticleCanvas />
      <ScanBeam />

      {/* Parallax ambient orbs */}
      <motion.div className="orb" style={{
        width:750, height:750, top:'-18%', left:'-12%',
        background:'radial-gradient(circle,rgba(0,212,255,.08) 0%,transparent 70%)',
        animation:'orbFloat1 32s ease-in-out infinite',
        x: orb1x, y: orb1y,
      }} />
      <motion.div className="orb" style={{
        width:580, height:580, top:'8%', right:'-14%',
        background:'radial-gradient(circle,rgba(139,92,246,.07) 0%,transparent 70%)',
        animation:'orbFloat2 40s ease-in-out infinite', animationDelay:'-14s',
        x: orb2x, y: orb2y,
      }} />
      <motion.div className="orb" style={{
        width:420, height:420, bottom:'0%', left:'26%',
        background:'radial-gradient(circle,rgba(0,212,255,.05) 0%,transparent 70%)',
        animation:'orbFloat3 26s ease-in-out infinite', animationDelay:'-8s',
        x: orb3x, y: orb3y,
      }} />
      <div className="orb" style={{
        width:320, height:320, bottom:'-6%', right:'14%',
        background:'radial-gradient(circle,rgba(255,0,102,.04) 0%,transparent 70%)',
        animation:'orbFloat4 44s ease-in-out infinite', animationDelay:'-22s',
      }} />

      {/* HUD corners */}
      <CornerAccent pos="tl" />
      <CornerAccent pos="tr" />
      <CornerAccent pos="bl" />
      <CornerAccent pos="br" />

      {/* Main row: sidebar + chat */}
      <div className="flex flex-1 overflow-hidden" style={{ position:'relative', zIndex:4 }}>
        <div className="w-60 flex-shrink-0 h-full">
          <Sidebar
            onConversationSelect={handleConversationSelect}
            activeConvId={activeConvId}
            onNewChat={handleNewChat}
            selectedFile={selectedFile}
            onFileSelect={setSelectedFile}
          />
        </div>
        <div className="flex-1 h-full overflow-hidden">
          <ChatArea
            messages={messages}
            setMessages={setMessages}
            conversationId={conversationId}
            setConversationId={setConversationId}
            selectedFile={selectedFile}
          />
        </div>
      </div>

      {/* HUD bottom status bar */}
      <HudStatusBar />
    </div>
  )
}
