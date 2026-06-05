import api from './client'

export const login = (email, password) =>
  api.post('/login', { email, password })

export const signup = (email, password) =>
  api.post('/signup', { email, password })

export const validateToken = () =>
  api.get('/validate-token')

export const forgotPassword = (email) =>
  api.post('/forgot-password', { email })

export const resetPassword = (token, new_password) =>
  api.post('/reset-password', { token, new_password })
