import { useState } from 'react'
import { Shield, LayoutDashboard, FileSearch, Package, Settings, Plus, Bell, Search } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import DSARList from './pages/DSARList'
import CreateDSAR from './pages/CreateDSAR'
import DiscoveryPage from './pages/DiscoveryPage'

type Page = 'dashboard' | 'dsar' | 'create' | 'discovery'

function App() {
  const [page, setPage] = useState<Page>('dashboard')

  const navItems = [
    { id: 'dashboard' as Page, icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'dsar' as Page, icon: FileSearch, label: 'DSAR Requests' },
    { id: 'create' as Page, icon: Plus, label: 'New Request' },
    { id: 'discovery' as Page, icon: Shield, label: 'Data Discovery' },
  ]

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-dark-900 border-r border-dark-700 flex flex-col">
        <div className="p-4 border-b border-dark-700">
          <div className="flex items-center gap-2">
            <Shield className="w-8 h-8 text-accent-500" />
            <div>
              <h1 className="text-lg font-bold text-white">DataGuard</h1>
              <p className="text-xs text-dark-400">DSAR Automator</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setPage(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                page === item.id
                  ? 'bg-accent-600 text-white'
                  : 'text-dark-300 hover:bg-dark-800 hover:text-white'
              }`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}
        </nav>
        <div className="p-3 border-t border-dark-700">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-dark-800">
            <div className="w-8 h-8 rounded-full bg-accent-600 flex items-center justify-center text-white text-sm font-medium">
              DP
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white truncate">DPO Admin</p>
              <p className="text-xs text-dark-400 truncate">dpo@company.com</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <header className="sticky top-0 z-10 bg-dark-900/80 backdrop-blur border-b border-dark-700 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-dark-400" />
              <input
                type="text"
                placeholder="Search requests..."
                className="pl-9 pr-4 py-2 bg-dark-800 border border-dark-600 rounded-lg text-sm text-white placeholder-dark-400 focus:outline-none focus:border-accent-500 w-64"
              />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button className="relative p-2 text-dark-300 hover:text-white hover:bg-dark-800 rounded-lg">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-danger rounded-full" />
            </button>
          </div>
        </header>

        <div className="p-6">
          {page === 'dashboard' && <Dashboard />}
          {page === 'dsar' && <DSARList />}
          {page === 'create' && <CreateDSAR />}
          {page === 'discovery' && <DiscoveryPage />}
        </div>
      </main>
    </div>
  )
}

export default App
