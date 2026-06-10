import { useAuth, AuthProvider } from './context/AuthContext'
import LoginPage from './components/Auth/LoginPage'
import AppLayout from './components/Layout/AppLayout'
import Spinner from './components/UI/Spinner'
import { CustomCursor, ClickBurstCanvas } from './components/UI/GlobalEffects'

function AppInner() {
  const { isLoggedIn, loading } = useAuth()

  if (loading) {
    return (
      <div className="mesh-bg h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #6366F1, #8B5CF6)', boxShadow: '0 0 24px rgba(99,102,241,0.4)' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <Spinner size={20} className="text-indigo-400" />
        </div>
      </div>
    )
  }

  return isLoggedIn ? <AppLayout /> : <LoginPage />
}

export default function App() {
  return (
    <AuthProvider>
      <CustomCursor />
      <ClickBurstCanvas />
      <AppInner />
    </AuthProvider>
  )
}
