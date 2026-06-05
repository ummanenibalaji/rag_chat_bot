import { createContext, useContext, useState, useEffect } from 'react'
import { validateToken } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) { setLoading(false); return }
    validateToken()
      .then(({ data }) => {
        if (data.valid) setEmail(data.email)
        else logout()
      })
      .catch(logout)
      .finally(() => setLoading(false))
  }, [])

  const loginSuccess = (accessToken, userEmail) => {
    localStorage.setItem('token', accessToken)
    setToken(accessToken)
    setEmail(userEmail)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setEmail('')
  }

  return (
    <AuthContext.Provider value={{ token, email, loading, loginSuccess, logout, isLoggedIn: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
