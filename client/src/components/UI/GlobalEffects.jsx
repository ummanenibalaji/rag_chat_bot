import { useEffect, useRef } from 'react'

export function CustomCursor() {
  const dotRef  = useRef(null)
  const ringRef = useRef(null)
  const posRef  = useRef({ x: -200, y: -200 })
  const ringPos = useRef({ x: -200, y: -200 })
  const state   = useRef({ hover: false, click: false })

  useEffect(() => {
    const onMove = (e) => { posRef.current = { x: e.clientX, y: e.clientY } }
    const onDown = () => { state.current.click = true }
    const onUp   = () => { state.current.click = false }
    const onOver = (e) => {
      state.current.hover = !!e.target.closest('button,a,[role="button"],input,textarea,select')
    }

    document.addEventListener('mousemove', onMove)
    document.addEventListener('mousemove', onOver)
    document.addEventListener('mousedown', onDown)
    document.addEventListener('mouseup',   onUp)

    let raf
    const tick = () => {
      const { x, y } = posRef.current
      const h = state.current.hover
      const c = state.current.click
      const dot  = dotRef.current
      const ring = ringRef.current
      if (dot && ring) {
        dot.style.transform  = `translate(${x - 4}px,${y - 4}px) scale(${c ? 0.45 : h ? 1.4 : 1})`
        dot.style.background = h ? '#FF0066' : '#00D4FF'
        dot.style.boxShadow  = h
          ? '0 0 14px #FF0066,0 0 28px rgba(255,0,102,.55)'
          : '0 0 14px #00D4FF,0 0 28px rgba(0,212,255,.5)'

        ringPos.current.x += (x - ringPos.current.x) * 0.13
        ringPos.current.y += (y - ringPos.current.y) * 0.13
        const sz = h ? 46 : c ? 22 : 32
        ring.style.transform   = `translate(${ringPos.current.x - sz/2}px,${ringPos.current.y - sz/2}px) scale(${c ? 0.65 : 1})`
        ring.style.width       = sz + 'px'
        ring.style.height      = sz + 'px'
        ring.style.borderColor = h ? 'rgba(255,0,102,.6)' : 'rgba(0,212,255,.35)'
        ring.style.boxShadow   = h ? '0 0 20px rgba(255,0,102,.22)' : '0 0 12px rgba(0,212,255,.1)'
      }
      raf = requestAnimationFrame(tick)
    }
    tick()

    return () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mousemove', onOver)
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('mouseup',   onUp)
      cancelAnimationFrame(raf)
    }
  }, [])

  return (
    <>
      <div ref={dotRef} style={{
        position:'fixed', width:8, height:8, borderRadius:'50%',
        pointerEvents:'none', zIndex:999999, mixBlendMode:'screen',
        transition:'background .12s,box-shadow .12s,transform .08s',
        willChange:'transform',
      }} />
      <div ref={ringRef} style={{
        position:'fixed', borderRadius:'50%',
        border:'1px solid rgba(0,212,255,.35)',
        pointerEvents:'none', zIndex:999998,
        transition:'width .18s,height .18s,border-color .18s,box-shadow .18s',
        willChange:'transform,width,height',
      }} />
    </>
  )
}

export function ClickBurstCanvas() {
  const ref = useRef(null)
  useEffect(() => {
    const c   = ref.current
    const ctx = c.getContext('2d')
    let raf
    const resize = () => { c.width = window.innerWidth; c.height = window.innerHeight }
    resize()
    window.addEventListener('resize', resize)

    const particles = []
    const burst = (x, y) => {
      const HUES = [190, 270, 340]
      for (let i = 0; i < 16; i++) {
        const angle = (i / 16) * Math.PI * 2 + Math.random() * .4
        const spd   = Math.random() * 4 + 1.5
        particles.push({
          x, y,
          vx: Math.cos(angle) * spd,
          vy: Math.sin(angle) * spd,
          r: Math.random() * 2.2 + .8,
          hue: HUES[Math.floor(Math.random() * 3)],
          life: 1,
          decay: Math.random() * .032 + .018,
        })
      }
    }

    const onClick = (e) => burst(e.clientX, e.clientY)
    window.addEventListener('click', onClick)

    const draw = () => {
      ctx.clearRect(0, 0, c.width, c.height)
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i]
        p.x += p.vx; p.y += p.vy
        p.vx *= .91;  p.vy *= .91
        p.life -= p.decay
        if (p.life <= 0) { particles.splice(i, 1); continue }
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r * p.life, 0, Math.PI * 2)
        ctx.fillStyle = `hsla(${p.hue},100%,72%,${p.life})`
        ctx.fill()
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.r * p.life * 4.5, 0, Math.PI * 2)
        ctx.fillStyle = `hsla(${p.hue},100%,65%,${p.life * .1})`
        ctx.fill()
      }
      raf = requestAnimationFrame(draw)
    }
    draw()

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', resize)
      window.removeEventListener('click', onClick)
    }
  }, [])

  return (
    <canvas ref={ref} style={{ position:'fixed', inset:0, pointerEvents:'none', zIndex:999997 }} />
  )
}
