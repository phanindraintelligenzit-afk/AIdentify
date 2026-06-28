import { useState } from 'react'
import { Search, Filter, ChevronRight, AlertTriangle, CheckCircle, Clock } from 'lucide-react'

const mockDSARs = [
  { id: 'DSAR-20260628-0001', requester: 'Jane Smith', email: 'jane@example.com', type: 'access', regulation: 'GDPR', status: 'reviewing', days: 3, risk: 'high', received: '2026-06-28' },
  { id: 'DSAR-20260625-0003', requester: 'John Doe', email: 'john@example.com', type: 'erasure', regulation: 'CCPA', status: 'discovering', days: 7, risk: 'medium', received: '2026-06-25' },
  { id: 'DSAR-20260620-0005', requester: 'Alice Brown', email: 'alice@example.com', type: 'access', regulation: 'GDPR', status: 'approving', days: 12, risk: 'low', received: '2026-06-20' },
  { id: 'DSAR-20260618-0007', requester: 'Bob Wilson', email: 'bob@example.com', type: 'portability', regulation: 'GDPR', status: 'completed', days: 15, risk: 'low', received: '2026-06-18' },
  { id: 'DSAR-20260615-0009', requester: 'Carol Davis', email: 'carol@example.com', type: 'rectification', regulation: 'CCPA', status: 'received', days: 18, risk: 'low', received: '2026-06-15' },
  { id: 'DSAR-20260612-0011', requester: 'David Lee', email: 'david@example.com', type: 'access', regulation: 'GDPR', status: 'completed', days: 21, risk: 'low', received: '2026-06-12' },
  { id: 'DSAR-20260610-0013', requester: 'Eva Martinez', email: 'eva@example.com', type: 'erasure', regulation: 'GDPR', status: 'completed', days: 23, risk: 'low', received: '2026-06-10' },
  { id: 'DSAR-20260608-0015', requester: 'Frank Chen', email: 'frank@example.com', type: 'access', regulation: 'CCPA', status: 'completed', days: 25, risk: 'low', received: '2026-06-08' },
]

const statusColors: Record<string, string> = {
  received: 'bg-dark-600 text-dark-200',
  discovering: 'bg-accent-600/20 text-accent-400',
  reviewing: 'bg-warning/20 text-warning',
  approving: 'bg-purple-500/20 text-purple-300',
  completed: 'bg-success/20 text-success',
}

const riskColors: Record<string, string> = {
  high: 'text-danger',
  medium: 'text-warning',
  low: 'text-success',
}

export default function DSARList() {
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')

  const filtered = mockDSARs.filter((d) => {
    const matchSearch = d.requester.toLowerCase().includes(search.toLowerCase()) || d.id.toLowerCase().includes(search.toLowerCase())
    const matchStatus = filterStatus === 'all' || d.status === filterStatus
    return matchSearch && matchStatus
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">DSAR Requests</h2>
        <p className="text-dark-400 mt-1">Manage and track all data subject access requests</p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-dark-400" />
          <input
            type="text"
            placeholder="Search by name or reference..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-dark-900 border border-dark-600 rounded-lg text-sm text-white placeholder-dark-400 focus:outline-none focus:border-accent-500"
          />
        </div>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-2 bg-dark-900 border border-dark-600 rounded-lg text-sm text-white focus:outline-none focus:border-accent-500"
        >
          <option value="all">All Status</option>
          <option value="received">Received</option>
          <option value="discovering">Discovering</option>
          <option value="reviewing">Reviewing</option>
          <option value="approving">Approving</option>
          <option value="completed">Completed</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-dark-900 border border-dark-700 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="text-left px-4 py-3 text-xs font-medium text-dark-400 uppercase">Reference</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-dark-400 uppercase">Requester</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-dark-400 uppercase">Type</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-dark-400 uppercase">Status</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-dark-400 uppercase">Risk</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-dark-400 uppercase">Days Left</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-dark-400 uppercase"></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((dsar) => (
              <tr key={dsar.id} className="border-b border-dark-700/50 hover:bg-dark-800/50 transition-colors">
                <td className="px-4 py-3">
                  <p className="text-sm font-mono text-white">{dsar.id}</p>
                  <p className="text-xs text-dark-400">{dsar.received}</p>
                </td>
                <td className="px-4 py-3">
                  <p className="text-sm text-white">{dsar.requester}</p>
                  <p className="text-xs text-dark-400">{dsar.email}</p>
                </td>
                <td className="px-4 py-3">
                  <p className="text-sm text-dark-200 capitalize">{dsar.type}</p>
                  <p className="text-xs text-dark-400">{dsar.regulation}</p>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[dsar.status]}`}>
                    {dsar.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs font-medium ${riskColors[dsar.risk]}`}>
                    {dsar.risk}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <p className={`text-sm font-medium ${dsar.days <= 5 ? 'text-danger' : dsar.days <= 10 ? 'text-warning' : 'text-dark-200'}`}>
                    {dsar.days}d
                  </p>
                </td>
                <td className="px-4 py-3">
                  <ChevronRight className="w-4 h-4 text-dark-400" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="text-center py-8 text-dark-400">No requests found</div>
        )}
      </div>
    </div>
  )
}
