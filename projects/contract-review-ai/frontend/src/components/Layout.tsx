import React from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { Sidebar, Header } from './Sidebar'
import { useAuth } from '../contexts/AuthContext'

export const Layout = () => {
  const { user, logout } = useAuth()
  const location = useLocation()
  
  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header user={user} onLogout={logout} />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export const Sidebar = () => {
  const location = useLocation()
  const { user } = useAuth()
  
  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: 'LayoutDashboard' },
    { href: '/upload', label: 'Upload Contract', icon: 'Upload' },
    { href: '/playbooks', label: 'Playbooks', icon: 'BookOpen' },
    { href: '/settings', label: 'Settings', icon: 'Settings' },
  ]
  
  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col hidden lg:flex">
      <div className="p-6 border-b border-border">
        <h1 className="text-xl font-bold text-primary">Contract Review AI</h1>
        <p className="text-sm text-muted-foreground mt-1">AI-powered contract analysis</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.href}
            to={item.href}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              }`
            }
          >
            <span className="text-lg">{getIcon(item.icon)}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
            {user?.full_name?.[0] || user?.email?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.full_name || 'User'}</p>
            <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
          </div>
        </div>
      </div>
    </aside>
  )
}

export const Header = ({ user, onLogout }: { user: any; onLogout: () => void }) => {
  return (
    <header className="h-16 bg-card border-b border-border flex items-center justify-between px-6 sticky top-0 z-10">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold">Contract Review AI</h2>
      </div>
      <div className="flex items-center gap-4">
        <button onClick={onLogout} className="text-sm text-muted-foreground hover:text-foreground">
          Logout
        </button>
      </div>
    </header>
  )
}

function getIcon(name: string): string {
  const icons: Record<string, string> = {
    LayoutDashboard: '📊',
    Upload: '📤',
    BookOpen: '📖',
    Settings: '⚙️',
  }
  return icons[name] || '📄'
}