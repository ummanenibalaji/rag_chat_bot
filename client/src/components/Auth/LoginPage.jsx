import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { login, signup, forgotPassword } from '../../api/auth'
import { useAuth } from '../../context/AuthContext'
import Spinner from '../UI/Spinner'

/* ─── Hero particle field ─── */
function HeroParticles() {
  const ref = useRef(null)
  useEffect(() => {
    const c = ref.current, ctx = c.getContext('2d')
    let id
    const resize = () => { c.width = c.offsetWidth; c.height = c.offsetHeight }
    resize()
    window.addEventListener('resize', resize)
    const pts = Array.from({ length: 65 }, () => ({
      x: Math.random() * c.width, y: Math.random() * c.height,
      vx: (Math.random() - .5) * .22, vy: (Math.random() - .5) * .22,
      r: Math.random() * 1.5 + .3,
      hue: Math.random() < .65 ? 190 : 272,
      ph: Math.random() * Math.PI * 2,
    }))
    let t = 0
    function frame() {
      ctx.clearRect(0, 0, c.width, c.height)
      t += .004
      pts.forEach((p, i) => {
        p.x += p.vx; p.y += p.vy
        if (p.x < 0) p.x = c.width; if (p.x > c.width) p.x = 0
        if (p.y < 0) p.y = c.height; if (p.y > c.height) p.y = 0
        const pulse = .55 + .45 * Math.sin(t * 1.7 + p.ph)
        for (let j = i + 1; j < pts.length; j++) {
          const q = pts[j], dx = p.x - q.x, dy = p.y - q.y
          const d = Math.sqrt(dx*dx + dy*dy)
          if (d < 115) {
            const g = ctx.createLinearGradient(p.x, p.y, q.x, q.y)
            g.addColorStop(0, `hsla(${p.hue},100%,65%,${(1-d/115)*.065*pulse})`)
            g.addColorStop(1, `hsla(${q.hue},100%,65%,${(1-d/115)*.065*pulse})`)
            ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y)
            ctx.strokeStyle = g; ctx.lineWidth = .5; ctx.stroke()
          }
        }
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI*2)
        ctx.fillStyle = `hsla(${p.hue},100%,72%,${.28*pulse})`; ctx.fill()
      })
      id = requestAnimationFrame(frame)
    }
    frame()
    return () => { cancelAnimationFrame(id); window.removeEventListener('resize', resize) }
  }, [])
  return <canvas ref={ref} style={{ position:'absolute', inset:0, width:'100%', height:'100%', pointerEvents:'none', zIndex:0 }} />
}

/* ─── Holographic globe ─── */
const RINGS = [
  { size:290, rx:72, ry:0,    dur:14, rev:false, color:'#00D4FF', dot:6 },
  { size:285, rx:50, ry:42,   dur:20, rev:true,  color:'#8B5CF6', dot:5 },
  { size:275, rx:80, ry:-28,  dur:28, rev:false, color:'#00D4FF', dot:4 },
  { size:258, rx:60, ry:85,   dur:35, rev:true,  color:'#FF0066', dot:4 },
  { size:240, rx:88, ry:15,   dur:44, rev:false, color:'#8B5CF6', dot:3 },
]
function HoloGlobe() {
  return (
    <div style={{ position:'relative', width:300, height:300 }}>
      {/* Outer bloom layers */}
      <div style={{ position:'absolute', inset:-50, borderRadius:'50%',
        background:'radial-gradient(circle,rgba(0,212,255,.1) 0%,transparent 62%)',
        filter:'blur(28px)', animation:'breathe 5s ease-in-out infinite' }} />
      <div style={{ position:'absolute', inset:-30, borderRadius:'50%',
        background:'radial-gradient(circle,rgba(139,92,246,.07) 0%,transparent 60%)',
        filter:'blur(18px)', animation:'breathe 7s ease-in-out infinite', animationDelay:'-3s' }} />
      {/* Sphere body */}
      <div style={{
        position:'absolute', top:12, left:12, right:12, bottom:12, borderRadius:'50%',
        background:`radial-gradient(circle at 36% 30%,
          rgba(0,212,255,.24) 0%, rgba(0,212,255,.1) 22%,
          rgba(139,92,246,.12) 48%, rgba(0,1,8,.96) 100%)`,
        boxShadow:`0 0 80px rgba(0,212,255,.24),0 0 160px rgba(0,212,255,.09),
          inset 0 0 70px rgba(0,212,255,.07),inset 0 0 20px rgba(139,92,246,.05)`,
        overflow:'hidden',
      }}>
        {/* Latitude/longitude grid */}
        <div style={{ position:'absolute', inset:0, borderRadius:'50%',
          backgroundImage:`
            repeating-linear-gradient(0deg,transparent,transparent 25px,rgba(0,212,255,.045) 25px,rgba(0,212,255,.045) 26px),
            repeating-linear-gradient(90deg,transparent,transparent 25px,rgba(0,212,255,.045) 25px,rgba(0,212,255,.045) 26px)` }} />
        {/* Specular highlight */}
        <div style={{ position:'absolute', top:'13%', left:'20%', width:'30%', height:'20%',
          background:'radial-gradient(ellipse,rgba(255,255,255,.09) 0%,transparent 70%)',
          borderRadius:'50%', transform:'rotate(-25deg)' }} />
        <div style={{ position:'absolute', bottom:'20%', right:'18%', width:'16%', height:'10%',
          background:'radial-gradient(ellipse,rgba(139,92,246,.12) 0%,transparent 70%)',
          borderRadius:'50%' }} />
      </div>
      {/* Orbital rings */}
      <div style={{ position:'absolute', inset:0, perspective:'900px' }}>
        {RINGS.map((r, i) => (
          <div key={i} style={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center',
            transform:`rotateX(${r.rx}deg) rotateY(${r.ry}deg)` }}>
            <div style={{ width:r.size, height:r.size, borderRadius:'50%', position:'relative',
              border:`1px solid ${r.color}${i < 2 ? '30' : '20'}`,
              animation:`${r.rev?'orbitCCW':'orbit'} ${r.dur}s linear infinite` }}>
              <div style={{ position:'absolute', top:-(r.dot/2), left:'50%', transform:'translateX(-50%)',
                width:r.dot, height:r.dot, borderRadius:'50%', background:r.color,
                boxShadow:`0 0 ${r.dot*2}px ${r.color},0 0 ${r.dot*5}px ${r.color}60` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ─── Glitch wordmark ─── */
function GlitchWordmark({ size = '3.6rem' }) {
  return (
    <div style={{ position:'relative', display:'inline-flex', alignItems:'baseline', userSelect:'none', lineHeight:1 }}>
      <span style={{ fontWeight:900, fontSize:size, letterSpacing:'-0.05em', color:'#fff',
        textShadow:'0 0 40px rgba(0,212,255,.35)' }}>DOC</span>
      <span className="ai-wordmark" style={{ fontWeight:900, fontSize:size, letterSpacing:'-0.05em',
        filter:'drop-shadow(0 0 20px rgba(0,212,255,.55))' }}>ai</span>
      <span style={{ position:'absolute', inset:0, fontWeight:900, fontSize:size, letterSpacing:'-0.05em',
        color:'rgba(0,212,255,.4)', animation:'glitch1 7s step-end infinite', pointerEvents:'none', mixBlendMode:'screen' }}>DOCai</span>
      <span style={{ position:'absolute', inset:0, fontWeight:900, fontSize:size, letterSpacing:'-0.05em',
        color:'rgba(255,0,102,.22)', animation:'glitch2 7s step-end infinite', pointerEvents:'none' }}>DOCai</span>
    </div>
  )
}

/* ─── Metric chip ─── */
function MetricChip({ label, value, color='#00D4FF', live=false }) {
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:3, padding:'8px 14px', borderRadius:10,
      background:`${color}06`, border:`1px solid ${color}15`,
      boxShadow:`0 2px 16px rgba(0,0,0,.2),0 0 20px ${color}05` }}>
      <span className="data-stream" style={{ color:`${color}45`, fontSize:'7.5px' }}>{label}</span>
      <div style={{ display:'flex', alignItems:'center', gap:5 }}>
        <span style={{ color, fontWeight:700, fontSize:'13px', fontFamily:"'Space Grotesk',sans-serif",
          textShadow:`0 0 14px ${color}50`, letterSpacing:'.02em' }}>{value}</span>
        {live && <div style={{ width:4, height:4, borderRadius:'50%', background:'#00FF88',
          boxShadow:'0 0 6px #00FF88,0 0 12px rgba(0,255,136,.4)', animation:'breathe 1.4s ease-in-out infinite' }} />}
      </div>
    </div>
  )
}

/* ─── Terminal input ─── */
function TerminalInput({ label, type='text', value, onChange, placeholder, autoComplete }) {
  const [focused, setFocused] = useState(false)
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
      <label className="data-stream" style={{
        color: focused ? 'rgba(0,212,255,.62)' : 'rgba(0,212,255,.28)',
        transition:'color .2s', paddingLeft:2, fontSize:'8.5px',
      }}>{label}</label>
      <div style={{
        position:'relative',
        border: focused ? '1px solid rgba(0,212,255,.45)' : '1px solid rgba(0,212,255,.1)',
        borderRadius:12,
        background: focused ? 'rgba(0,14,34,.9)' : 'rgba(0,4,16,.72)',
        boxShadow: focused
          ? '0 0 0 1px rgba(0,212,255,.07),0 0 32px rgba(0,212,255,.07),inset 0 1px 0 rgba(0,212,255,.06)'
          : 'inset 0 1px 0 rgba(0,212,255,.025)',
        transition:'all .22s ease',
      }}>
        <div style={{
          position:'absolute', left:0, top:0, bottom:0, width:2,
          borderRadius:'12px 0 0 12px',
          background: focused ? 'linear-gradient(180deg,#00D4FF,#8B5CF6)' : 'transparent',
          boxShadow: focused ? '0 0 10px rgba(0,212,255,.7)' : 'none',
          transition:'all .22s ease',
        }} />
        <input type={type} value={value} onChange={onChange} placeholder={placeholder}
          autoComplete={autoComplete}
          onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
          style={{
            width:'100%', padding:'12px 16px 12px 18px',
            background:'transparent', border:'none', outline:'none',
            color:'rgba(210,240,255,.9)', fontSize:'13.5px',
            letterSpacing:'-0.01em', caretColor:'#00D4FF',
          }} />
      </div>
    </div>
  )
}

/* ─── Data node ─── */
function DataNode({ top, left, value, label, color='#00D4FF', delay=0 }) {
  return (
    <motion.div
      initial={{ opacity:0, scale:.6 }}
      animate={{ opacity:1, scale:1 }}
      transition={{ delay, duration:.6, ease:[.16,1,.3,1] }}
      style={{ position:'absolute', top, left, display:'flex', flexDirection:'column', alignItems:'center', gap:3 }}
    >
      <div style={{ width:34, height:34, borderRadius:10, display:'flex', alignItems:'center',
        justifyContent:'center', flexDirection:'column',
        background:`rgba(${color==='#00D4FF'?'0,212,255':color==='#8B5CF6'?'139,92,246':'255,0,102'},.06)`,
        border:`1px solid ${color}20`,
        boxShadow:`0 0 20px ${color}10,inset 0 1px 0 ${color}08` }}>
        <span style={{ fontFamily:"'Space Grotesk',sans-serif", fontWeight:700, fontSize:'9px',
          color, lineHeight:1, letterSpacing:'.03em' }}>{value}</span>
        <span className="data-stream" style={{ color:`${color}45`, fontSize:'6px', marginTop:1 }}>{label}</span>
      </div>
      {/* Connecting line to sphere */}
      <div style={{ width:1, height:14, background:`linear-gradient(180deg,${color}25,transparent)` }} />
    </motion.div>
  )
}

/* ─── Main export ─── */
export default function LoginPage() {
  const { loginSuccess: authLogin } = useAuth()
  const [mode, setMode]       = useState('login')
  const [email, setEmail]     = useState('')
  const [password, setPassword] = useState('')
  const [name, setName]       = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError]     = useState('')
  const [msg, setMsg]         = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError(''); setMsg(''); setLoading(true)
    try {
      if (mode === 'login') {
        const resp = await login(email, password)
        if (!resp.data?.access_token) throw new Error(resp.data?.message || 'Invalid credentials')
        authLogin(resp.data.access_token, email)
      } else if (mode === 'signup') {
        if (password !== confirm) { setError('Passwords do not match'); setLoading(false); return }
        const sr = await signup(email, password)
        if (sr.data?.message?.toLowerCase().includes('already')) throw new Error(sr.data.message)
        setMsg('Account created. Sign in to continue.')
        setMode('login')
      } else {
        await forgotPassword(email)
        setMsg('Reset link sent to your email.')
      }
    } catch(err) {
      setError(err?.response?.data?.detail || err.message || 'Error')
    }
    setLoading(false)
  }

  return (
    <div style={{ display:'flex', height:'100vh', background:'var(--void)', overflow:'hidden', position:'relative' }}>

      {/* ═══ LEFT HERO PANEL ═══ */}
      <motion.div
        initial={{ opacity:0 }}
        animate={{ opacity:1 }}
        transition={{ duration:.8 }}
        style={{ flex:'0 0 58%', position:'relative', display:'flex', flexDirection:'column',
          alignItems:'center', justifyContent:'center', overflow:'hidden',
          borderRight:'1px solid rgba(0,212,255,.06)' }}
      >
        <HeroParticles />

        {/* Hex grid overlay */}
        <div className="hex-bg" style={{ position:'absolute', inset:0, pointerEvents:'none', zIndex:1 }} />

        {/* Ambient gradient pools */}
        <div style={{ position:'absolute', top:'-10%', left:'-5%', width:500, height:500, borderRadius:'50%',
          background:'radial-gradient(circle,rgba(0,212,255,.07) 0%,transparent 65%)',
          filter:'blur(60px)', pointerEvents:'none', zIndex:1 }} />
        <div style={{ position:'absolute', bottom:'5%', right:'-10%', width:400, height:400, borderRadius:'50%',
          background:'radial-gradient(circle,rgba(139,92,246,.07) 0%,transparent 65%)',
          filter:'blur(50px)', pointerEvents:'none', zIndex:1 }} />

        {/* Version badge */}
        <motion.div
          initial={{ opacity:0, y:-12 }}
          animate={{ opacity:1, y:0 }}
          transition={{ delay:.3, duration:.5 }}
          style={{ position:'absolute', top:28, left:32, zIndex:4,
            display:'flex', alignItems:'center', gap:6,
            padding:'5px 12px', borderRadius:20,
            background:'rgba(0,212,255,.04)', border:'1px solid rgba(0,212,255,.12)',
            boxShadow:'0 0 16px rgba(0,212,255,.06)' }}
        >
          <div style={{ width:5, height:5, borderRadius:'50%', background:'#00FF88',
            boxShadow:'0 0 6px #00FF88', animation:'breathe 2s ease-in-out infinite' }} />
          <span className="data-stream" style={{ color:'rgba(0,212,255,.5)', letterSpacing:'.14em' }}>
            NEURAL ENGINE v2.4
          </span>
        </motion.div>

        {/* Globe + data nodes */}
        <div style={{ position:'relative', zIndex:3 }}>
          <motion.div
            initial={{ opacity:0, scale:.8 }}
            animate={{ opacity:1, scale:1 }}
            transition={{ delay:.2, duration:.9, ease:[.16,1,.3,1] }}
          >
            <HoloGlobe />
          </motion.div>

          {/* Floating data nodes */}
          <DataNode top="-18%" left="88%"  value="14.2K" label="VECS"  color="#00D4FF" delay={.7} />
          <DataNode top="12%"  left="-18%" value="99.7%" label="ACC"   color="#00FF88" delay={.85} />
          <DataNode top="78%"  left="90%"  value="2/2"   label="MDLS"  color="#8B5CF6" delay={1.0} />
          <DataNode top="82%"  left="-14%" value="142ms" label="LAT"   color="#FF0066" delay={1.1} />
        </div>

        {/* Wordmark + tagline */}
        <motion.div
          initial={{ opacity:0, y:14 }}
          animate={{ opacity:1, y:0 }}
          transition={{ delay:.5, duration:.6, ease:[.16,1,.3,1] }}
          style={{ zIndex:3, marginTop:28, textAlign:'center', display:'flex', flexDirection:'column', alignItems:'center', gap:8 }}
        >
          <GlitchWordmark size="3.6rem" />
          <div style={{ display:'flex', alignItems:'center', gap:10, marginTop:4 }}>
            <div style={{ width:28, height:1, background:'linear-gradient(90deg,transparent,rgba(0,212,255,.4))' }} />
            <span className="data-stream" style={{ color:'rgba(0,212,255,.38)', letterSpacing:'.2em', fontSize:'8.5px' }}>
              TRANSFORM DOCUMENTS INTO INTELLIGENCE
            </span>
            <div style={{ width:28, height:1, background:'linear-gradient(90deg,rgba(0,212,255,.4),transparent)' }} />
          </div>
        </motion.div>

        {/* Metric chips */}
        <motion.div
          initial={{ opacity:0, y:12 }}
          animate={{ opacity:1, y:0 }}
          transition={{ delay:.75, duration:.5 }}
          style={{ zIndex:3, marginTop:24, display:'grid', gridTemplateColumns:'1fr 1fr', gap:8 }}
        >
          <MetricChip label="VECTOR INDEX"  value="14,247"  color="#00D4FF" live />
          <MetricChip label="ACCURACY"      value="99.7 %"  color="#00FF88" />
          <MetricChip label="MODELS ONLINE" value="2 / 2"   color="#8B5CF6" live />
          <MetricChip label="AVG LATENCY"   value="142 ms"  color="#FF4466" />
        </motion.div>

        {/* Bottom system status */}
        <motion.div
          initial={{ opacity:0 }}
          animate={{ opacity:1 }}
          transition={{ delay:1, duration:.5 }}
          style={{ position:'absolute', bottom:20, left:0, right:0, zIndex:3,
            display:'flex', justifyContent:'center', gap:20 }}
        >
          {['HYBRID RETRIEVAL','CROSS-ENCODER','BM25 + FAISS'].map(s => (
            <div key={s} style={{ display:'flex', alignItems:'center', gap:5 }}>
              <div style={{ width:3, height:3, borderRadius:'50%', background:'rgba(0,212,255,.4)',
                boxShadow:'0 0 5px rgba(0,212,255,.5)' }} />
              <span className="data-stream" style={{ color:'rgba(0,212,255,.22)', fontSize:'7.5px' }}>{s}</span>
            </div>
          ))}
        </motion.div>
      </motion.div>

      {/* ═══ RIGHT FORM PANEL ═══ */}
      <motion.div
        initial={{ opacity:0, x:30 }}
        animate={{ opacity:1, x:0 }}
        transition={{ duration:.7, ease:[.16,1,.3,1] }}
        style={{ flex:'0 0 42%', display:'flex', alignItems:'center', justifyContent:'center',
          position:'relative', overflow:'hidden',
          background:'linear-gradient(135deg,rgba(0,3,12,.96) 0%,rgba(0,6,20,.98) 100%)' }}
      >
        {/* Subtle inner glow */}
        <div style={{ position:'absolute', top:'30%', left:'50%', width:300, height:300, borderRadius:'50%',
          background:'radial-gradient(circle,rgba(139,92,246,.04) 0%,transparent 65%)',
          filter:'blur(40px)', transform:'translateX(-50%)', pointerEvents:'none' }} />

        <div style={{ width:'100%', maxWidth:380, padding:'0 40px', position:'relative', zIndex:2 }}>

          {/* Header */}
          <motion.div
            initial={{ opacity:0, y:-10 }}
            animate={{ opacity:1, y:0 }}
            transition={{ delay:.35, duration:.5 }}
            style={{ marginBottom:36, textAlign:'center' }}
          >
            {/* Mini wordmark */}
            <div style={{ display:'inline-flex', alignItems:'baseline', gap:0, marginBottom:14 }}>
              <span style={{ fontWeight:900, fontSize:'1.6rem', letterSpacing:'-0.05em', color:'#fff',
                textShadow:'0 0 24px rgba(0,212,255,.25)' }}>DOC</span>
              <span className="ai-wordmark" style={{ fontWeight:900, fontSize:'1.6rem', letterSpacing:'-0.05em',
                filter:'drop-shadow(0 0 10px rgba(0,212,255,.45))' }}>ai</span>
            </div>

            <div style={{ marginBottom:6 }}>
              <span className="data-stream" style={{ color:'rgba(0,212,255,.35)', letterSpacing:'.18em', fontSize:'8px' }}>
                {mode === 'login' ? 'SECURE AUTHENTICATION' : mode === 'signup' ? 'CREATE ACCOUNT' : 'ACCOUNT RECOVERY'}
              </span>
            </div>

            {/* Terminal cursor line */}
            <div style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:6, opacity:.35 }}>
              <div style={{ flex:1, height:1, background:'linear-gradient(90deg,transparent,rgba(0,212,255,.3))' }} />
              <div style={{ width:6, height:6, borderRadius:1, background:'rgba(0,212,255,.6)',
                animation:'breathe .9s ease-in-out infinite' }} />
              <div style={{ flex:1, height:1, background:'linear-gradient(90deg,rgba(0,212,255,.3),transparent)' }} />
            </div>
          </motion.div>

          {/* Form card */}
          <motion.div
            initial={{ opacity:0, y:16 }}
            animate={{ opacity:1, y:0 }}
            transition={{ delay:.45, duration:.6, ease:[.16,1,.3,1] }}
            style={{
              background:'rgba(0,6,20,.7)',
              border:'1px solid rgba(0,212,255,.1)',
              borderRadius:20,
              padding:'28px 28px',
              boxShadow:`0 24px 80px rgba(0,0,0,.7),0 0 0 1px rgba(0,212,255,.04),
                inset 0 1px 0 rgba(0,212,255,.06),0 0 60px rgba(0,212,255,.03)`,
              backdropFilter:'blur(30px)',
              position:'relative', overflow:'hidden',
            }}
          >
            {/* Top-left corner accent */}
            <div style={{ position:'absolute', top:0, left:0, width:40, height:40, pointerEvents:'none' }}>
              <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                <path d="M2 20 L2 2 L20 2" stroke="rgba(0,212,255,.3)" strokeWidth="1" strokeLinecap="round"/>
              </svg>
            </div>
            <div style={{ position:'absolute', bottom:0, right:0, width:40, height:40, pointerEvents:'none', transform:'scale(-1)' }}>
              <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                <path d="M2 20 L2 2 L20 2" stroke="rgba(0,212,255,.18)" strokeWidth="1" strokeLinecap="round"/>
              </svg>
            </div>

            <AnimatePresence mode="wait">
              <motion.form
                key={mode}
                initial={{ opacity:0, x:10 }}
                animate={{ opacity:1, x:0 }}
                exit={{ opacity:0, x:-10 }}
                transition={{ duration:.22 }}
                onSubmit={submit}
                style={{ display:'flex', flexDirection:'column', gap:16 }}
              >
                {mode === 'signup' && (
                  <TerminalInput label="DISPLAY NAME" type="text" value={name}
                    onChange={e => setName(e.target.value)} placeholder="Your name" autoComplete="name" />
                )}

                <TerminalInput label="EMAIL ADDRESS" type="email" value={email}
                  onChange={e => setEmail(e.target.value)} placeholder="user@domain.com" autoComplete="email" />

                {mode !== 'forgot' && (
                  <TerminalInput label="PASSWORD" type="password" value={password}
                    onChange={e => setPassword(e.target.value)} placeholder="••••••••••••" autoComplete={mode==='login'?'current-password':'new-password'} />
                )}
                {mode === 'signup' && (
                  <TerminalInput label="CONFIRM PASSWORD" type="password" value={confirm}
                    onChange={e => setConfirm(e.target.value)} placeholder="••••••••••••" autoComplete="new-password" />
                )}

                {/* Feedback */}
                <AnimatePresence>
                  {error && (
                    <motion.div initial={{ opacity:0, height:0 }} animate={{ opacity:1, height:'auto' }} exit={{ opacity:0, height:0 }}
                      style={{ padding:'10px 14px', borderRadius:10, background:'rgba(255,60,80,.06)',
                        border:'1px solid rgba(255,60,80,.18)', color:'rgba(255,100,120,.75)', fontSize:'12px' }}>
                      ⚠ {error}
                    </motion.div>
                  )}
                  {msg && (
                    <motion.div initial={{ opacity:0, height:0 }} animate={{ opacity:1, height:'auto' }} exit={{ opacity:0, height:0 }}
                      style={{ padding:'10px 14px', borderRadius:10, background:'rgba(0,255,136,.04)',
                        border:'1px solid rgba(0,255,136,.18)', color:'rgba(0,255,136,.75)', fontSize:'12px' }}>
                      ✓ {msg}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Submit */}
                <motion.button
                  type="submit"
                  disabled={loading}
                  whileHover={{ scale:1.015, boxShadow:'0 0 50px rgba(0,212,255,.5),0 0 100px rgba(139,92,246,.2),0 6px 24px rgba(0,0,0,.5)' }}
                  whileTap={{ scale:.96 }}
                  style={{
                    marginTop:4, padding:'13px 24px', borderRadius:13,
                    background:'linear-gradient(135deg,#007AAA 0%,#00D4FF 45%,#8B5CF6 100%)',
                    border:'none', color:'#fff', fontWeight:700, fontSize:'12.5px',
                    letterSpacing:'.1em', fontFamily:"'Space Grotesk',sans-serif",
                    boxShadow:'0 0 28px rgba(0,212,255,.3),0 4px 18px rgba(0,0,0,.45)',
                    position:'relative', overflow:'hidden', cursor:'pointer',
                    transition:'box-shadow .2s',
                  }}
                >
                  {/* Shimmer */}
                  <div style={{ position:'absolute', top:'-50%', left:'-60%', width:'40%', height:'200%',
                    background:'linear-gradient(90deg,transparent,rgba(255,255,255,.12),transparent)',
                    transform:'skewX(-20deg)', animation:'shimmerDrift 3.5s ease-in-out infinite' }} />
                  <span style={{ position:'relative', zIndex:1 }}>
                    {loading ? <Spinner size={14} /> :
                      mode === 'login' ? 'AUTHENTICATE' :
                      mode === 'signup' ? 'CREATE ACCOUNT' : 'SEND RESET LINK'}
                  </span>
                </motion.button>
              </motion.form>
            </AnimatePresence>
          </motion.div>

          {/* Footer links */}
          <motion.div
            initial={{ opacity:0 }} animate={{ opacity:1 }} transition={{ delay:.8 }}
            style={{ marginTop:20, textAlign:'center', display:'flex', flexDirection:'column', gap:10 }}
          >
            {mode === 'login' && (
              <div style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:12 }}>
                <button onClick={() => { setMode('signup'); setError(''); setMsg('') }}
                  style={{ background:'none', border:'none', color:'rgba(0,212,255,.38)', fontSize:'11.5px',
                    letterSpacing:'.04em', fontFamily:"'Space Grotesk',sans-serif",
                    transition:'color .15s', cursor:'pointer' }}
                  onMouseEnter={e => e.currentTarget.style.color = 'rgba(0,212,255,.72)'}
                  onMouseLeave={e => e.currentTarget.style.color = 'rgba(0,212,255,.38)'}
                >
                  Create account
                </button>
                <div style={{ width:1, height:10, background:'rgba(0,212,255,.14)' }} />
                <button onClick={() => { setMode('forgot'); setError(''); setMsg('') }}
                  style={{ background:'none', border:'none', color:'rgba(0,212,255,.38)', fontSize:'11.5px',
                    letterSpacing:'.04em', fontFamily:"'Space Grotesk',sans-serif",
                    transition:'color .15s', cursor:'pointer' }}
                  onMouseEnter={e => e.currentTarget.style.color = 'rgba(0,212,255,.72)'}
                  onMouseLeave={e => e.currentTarget.style.color = 'rgba(0,212,255,.38)'}
                >
                  Forgot password
                </button>
              </div>
            )}
            {mode !== 'login' && (
              <button onClick={() => { setMode('login'); setError(''); setMsg('') }}
                style={{ background:'none', border:'none', color:'rgba(0,212,255,.38)', fontSize:'11.5px',
                  letterSpacing:'.04em', fontFamily:"'Space Grotesk',sans-serif",
                  transition:'color .15s', cursor:'pointer' }}
                onMouseEnter={e => e.currentTarget.style.color = 'rgba(0,212,255,.72)'}
                onMouseLeave={e => e.currentTarget.style.color = 'rgba(0,212,255,.38)'}
              >
                ← Back to sign in
              </button>
            )}
          </motion.div>
        </div>
      </motion.div>
    </div>
  )
}
