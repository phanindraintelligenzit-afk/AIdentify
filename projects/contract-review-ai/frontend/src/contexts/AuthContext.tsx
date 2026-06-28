import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api } from './services/api'
import { User, Token } from './types'

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Load token from localStorage on mount
    const storedToken = localStorage.getItem('auth_token')
    const storedUser = localStorage.getItem('auth_user')
    
    if (storedToken && storedUser) {
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
      api.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`
    }
    setLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    const response = await api.post<Token>('/auth/login', new URLSearchParams({
      username: email,
      password,
    }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    
    const { access_token } = response.data
    setToken(access_token)
    localStorage.setItem('auth_token', access_token)
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    
    await refreshUser()
  }

  const register = async (email: string, password: string, fullName?: string) => {
    await api.post<User>('/auth/register', { email, password, full_name: fullName })
    await login(email, password)
  }

  const refreshUser = async () => {
    try {
      const response = await api.get<User>('/auth/me')
      setUser(response.data)
      localStorage.setItem('auth_user', JSON.stringify(response.data))
    } catch {
      logout()
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
    delete api.defaults.headers.common['Authorization']
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}