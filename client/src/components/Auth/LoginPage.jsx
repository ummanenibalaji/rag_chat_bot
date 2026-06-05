import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { login, signup, forgotPassword, resetPassword } from '../../api/auth'
import { useAuth } from '../../context/AuthContext'
import Spinner from '../UI/Spinner'

// view: 'auth' | 'forgot' | 'reset'

export default function LoginPage() {
  const { loginSuccess } = useAuth()
  const [tab, setTab] = useState('login')
  const [view, setView] = useState('auth')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [resetToken, setResetToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Detect reset token in URL: ?token=xxx
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    if (token) {
      setResetToken(token)
      setView('reset')
      window.history.replaceState({}, '', window.location.pathname)
    }
  }, [])

  const reset = () => { setError(''); setSuccess('') }

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true); reset()
    try {
      const { data } = await login(email, password)
      if (data.access_token) {
        loginSuccess(data.access_token, email)
      } else {
        setError(data.message || 'Login failed')
      }
    } catch {
      setError('Server unreachable. Is backend running?')
    } finally {
      setLoading(false)
    }
  }

  const handleSignup = async (e) => {
    e.preventDefault()
    setLoading(true); reset()
    try {
      const { data } = await signup(email, password)
      setSuccess(data.message || 'Account created! Please login.')
      setTab('login')
    } catch {
      setError('Signup failed. Try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleForgotPassword = async (e) => {
    e.preventDefault()
    setLoading(true); reset()
    try {
      const { data } = await forgotPassword(email)
      setSuccess(data.message || 'Reset email sent! Check your inbox.')
    } catch {
      setError('Failed to send reset email. Try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleResetPassword = async (e) => {
    e.preventDefault()
    reset()
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    setLoading(true)
    try {
      const { data } = await resetPassword(resetToken, newPassword)
      setSuccess(data.message || 'Password reset! Please login.')
      setTimeout(() => { setView('auth'); setTab('login') }, 2000)
    } catch {
      setError('Reset failed. Link may be expired.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mesh-bg min-h-screen flex items-center justify-center p-4">
      {/* Orb decorations */}
      <div className="fixed top-20 left-20 w-72 h-72 rounded-full opacity-20 pointer-events-none"
        style={{ background: 'radial-gradient(circle, #6366F1, transparent 70%)' }} />
      <div className="fixed bottom-20 right-20 w-96 h-96 rounded-full opacity-10 pointer-events-none"
        style={{ background: 'radial-gradient(circle, #8B5CF6, transparent 70%)' }} />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4"
            style={{ background: 'linear-gradient(135deg, #6366F1, #8B5CF6)', boxShadow: '0 0 30px rgba(99,102,241,0.4)' }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gradient mb-1">DocuMind AI</h1>
          <p className="text-sm" style={{ color: '#64748B' }}>Intelligent document conversations</p>
        </div>

        {/* Card */}
        <div className="glass-card gradient-border-card p-8">
          <AnimatePresence mode="wait">

            {/* ── FORGOT PASSWORD VIEW ── */}
            {view === 'forgot' && (
              <motion.div key="forgot"
                initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
              >
                <button onClick={() => { setView('auth'); reset() }}
                  className="flex items-center gap-1.5 text-xs mb-5 transition-colors"
                  style={{ color: '#64748B' }}
                  onMouseEnter={e => e.currentTarget.style.color = '#94A3B8'}
                  onMouseLeave={e => e.currentTarget.style.color = '#64748B'}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="15 18 9 12 15 6"/>
                  </svg>
                  Back to login
                </button>

                <h2 className="font-semibold text-base mb-1" style={{ color: '#E2E8F0' }}>Reset your password</h2>
                <p className="text-xs mb-6" style={{ color: '#475569' }}>Enter your email and we'll send a reset link.</p>

                <form onSubmit={handleForgotPassword} className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium mb-2" style={{ color: '#94A3B8' }}>Email address</label>
                    <input type="email" className="glass-input" placeholder="you@example.com"
                      value={email} onChange={(e) => setEmail(e.target.value)} required />
                  </div>

                  {error && <Alert type="error">{error}</Alert>}
                  {success && <Alert type="success">{success}</Alert>}

                  <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2" disabled={loading}>
                    {loading && <Spinner size={16} />}
                    Send reset link
                  </button>
                </form>
              </motion.div>
            )}

            {/* ── RESET PASSWORD VIEW ── */}
            {view === 'reset' && (
              <motion.div key="reset"
                initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
              >
                <div className="flex items-center gap-2 mb-5">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                    style={{ background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.2)' }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#818CF8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                  </div>
                  <div>
                    <h2 className="font-semibold text-sm" style={{ color: '#E2E8F0' }}>Set new password</h2>
                    <p className="text-xs" style={{ color: '#475569' }}>Choose a strong password</p>
                  </div>
                </div>

                <form onSubmit={handleResetPassword} className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium mb-2" style={{ color: '#94A3B8' }}>New password</label>
                    <input type="password" className="glass-input" placeholder="••••••••"
                      value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-2" style={{ color: '#94A3B8' }}>Confirm password</label>
                    <input type="password" className="glass-input" placeholder="••••••••"
                      value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
                  </div>

                  {/* Password strength indicator */}
                  {newPassword && <PasswordStrength password={newPassword} />}

                  {error && <Alert type="error">{error}</Alert>}
                  {success && <Alert type="success">{success}</Alert>}

                  <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2" disabled={loading}>
                    {loading && <Spinner size={16} />}
                    Reset password
                  </button>
                </form>
              </motion.div>
            )}

            {/* ── LOGIN / SIGNUP VIEW ── */}
            {view === 'auth' && (
              <motion.div key="auth"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                {/* Tabs */}
                <div className="flex gap-1 p-1 rounded-xl mb-6" style={{ background: 'rgba(0,0,0,0.3)' }}>
                  {['login', 'signup'].map((t) => (
                    <button key={t} onClick={() => { setTab(t); reset() }}
                      className="flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all duration-200 capitalize"
                      style={tab === t
                        ? { background: 'linear-gradient(135deg, #6366F1, #8B5CF6)', color: 'white', boxShadow: '0 2px 8px rgba(99,102,241,0.3)' }
                        : { color: '#64748B' }
                      }
                    >{t}</button>
                  ))}
                </div>

                <AnimatePresence mode="wait">
                  <motion.form key={tab}
                    initial={{ opacity: 0, x: tab === 'login' ? -10 : 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: tab === 'login' ? 10 : -10 }}
                    transition={{ duration: 0.15 }}
                    onSubmit={tab === 'login' ? handleLogin : handleSignup}
                    className="space-y-4"
                  >
                    <div>
                      <label className="block text-xs font-medium mb-2" style={{ color: '#94A3B8' }}>Email address</label>
                      <input type="email" className="glass-input" placeholder="you@example.com"
                        value={email} onChange={(e) => setEmail(e.target.value)} required />
                    </div>
                    <div>
                      <label className="block text-xs font-medium mb-2" style={{ color: '#94A3B8' }}>Password</label>
                      <input type="password" className="glass-input" placeholder="••••••••"
                        value={password} onChange={(e) => setPassword(e.target.value)} required />
                    </div>

                    {/* Forgot password link — login tab only */}
                    {tab === 'login' && (
                      <div className="flex justify-end -mt-2">
                        <button type="button" onClick={() => { setView('forgot'); reset() }}
                          className="text-xs transition-colors"
                          style={{ color: '#6366F1' }}
                          onMouseEnter={e => e.currentTarget.style.color = '#818CF8'}
                          onMouseLeave={e => e.currentTarget.style.color = '#6366F1'}
                        >
                          Forgot password?
                        </button>
                      </div>
                    )}

                    {error && <Alert type="error">{error}</Alert>}
                    {success && <Alert type="success">{success}</Alert>}

                    <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2" disabled={loading}>
                      {loading && <Spinner size={16} />}
                      {tab === 'login' ? 'Sign in' : 'Create account'}
                    </button>
                  </motion.form>
                </AnimatePresence>
              </motion.div>
            )}

          </AnimatePresence>
        </div>

        <p className="text-center text-xs mt-6" style={{ color: '#334155' }}>
          Powered by RAG · FAISS · Claude AI
        </p>
      </motion.div>
    </div>
  )
}

function Alert({ type, children }) {
  const styles = {
    error: { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.2)', color: '#FCA5A5', icon: '⚠' },
    success: { bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.2)', color: '#6EE7B7', icon: '✓' },
  }
  const s = styles[type]
  return (
    <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm"
      style={{ background: s.bg, border: `1px solid ${s.border}`, color: s.color }}
    >
      <span>{s.icon}</span> {children}
    </motion.div>
  )
}

function PasswordStrength({ password }) {
  const checks = [
    { label: '6+ chars', pass: password.length >= 6 },
    { label: 'Uppercase', pass: /[A-Z]/.test(password) },
    { label: 'Number', pass: /\d/.test(password) },
    { label: 'Symbol', pass: /[^A-Za-z0-9]/.test(password) },
  ]
  const score = checks.filter(c => c.pass).length
  const colors = ['#EF4444', '#F97316', '#EAB308', '#10B981']
  const labels = ['Weak', 'Fair', 'Good', 'Strong']

  return (
    <div className="space-y-2">
      <div className="flex gap-1">
        {[0,1,2,3].map(i => (
          <div key={i} className="flex-1 h-1 rounded-full transition-all duration-300"
            style={{ background: i < score ? colors[score - 1] : 'rgba(255,255,255,0.08)' }} />
        ))}
      </div>
      <div className="flex items-center justify-between">
        <div className="flex gap-2 flex-wrap">
          {checks.map(c => (
            <span key={c.label} className="text-xs"
              style={{ color: c.pass ? '#10B981' : '#475569' }}>
              {c.pass ? '✓' : '○'} {c.label}
            </span>
          ))}
        </div>
        <span className="text-xs font-medium" style={{ color: colors[score - 1] || '#475569' }}>
          {score > 0 ? labels[score - 1] : ''}
        </span>
      </div>
    </div>
  )
}
