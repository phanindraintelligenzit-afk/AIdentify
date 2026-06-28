import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { AlertTriangle, CheckCircle, Clock, TrendingUp, Database, Shield } from 'lucide-react'

const timelineData = Array.from({ length: 14 }, (_, i) => ({
  date: `${28 - i}d`,
  received: Math.floor(Math.random() * 5) + 1,
  completed: Math.floor(Math.random() * 4),
}))

const categoryData = [
  { name: 'Personal Info', value: 45, color: '#3b82f6' },
  { name: 'Transactions', value: 38, color: '#22c55e' },
  { name: 'Communications', value: 28, color: '#f59e0b' },
  { name: 'Support', value: 15, color: '#8b5cf6' },
  { name: 'Financial', value: 12, color: '#ef4444' },
  { name: 'Marketing', value: 8, color: '#06b6d4' },
]

const statusData = [
  { name: 'Completed', value: 29, color: '#22c55e' },
  { name: 'Reviewing', value: 8, color: '#f59e0b' },
  { name: 'Discovering', value: 5, color: '#3b82f6' },
  { name: 'Received', value: 3, color: '#8b5cf6' },
  { name: 'Approving', value: 2, color: '#06b6d4' },
]

const upcomingDeadlines = [
  { ref: 'DSAR-20260628-0001', requester: 'Jane Smith', days: 3, risk: 'high' },
  { ref: 'DSAR-20260625-0003', requester: 'John Doe', days: 7, risk: 'medium' },
  { ref: 'DSAR-20260620-0005', requester: 'Alice Brown', days: 12, risk: 'low' },
  { ref: 'DSAR-20260618-0007', requester: 'Bob Wilson', days: 15, risk: 'low' },
]

export default function Dashboard() {
  const stats = [
    { label: 'Total Requests', value: 47, icon: Shield, color: 'text-accent-400', bg: 'bg-accent-500/10' },
    { label: 'Pending', value: 8, icon: Clock, color: 'text-warning', bg: 'bg-warning/10' },
    { label: 'Completed', value: 29, icon: CheckCircle, color: 'text-success', bg: 'bg-success/10' },
    { label: 'Overdue', value: 1, icon: AlertTriangle, color: 'text-danger', bg: 'bg-danger/10' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Dashboard</h2>
        <p className="text-dark-400 mt-1">GDPR/CCPA DSAR compliance overview</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-dark-900 border border-dark-700 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-dark-400">{stat.label}</p>
                <p className="text-3xl font-bold text-white mt-1">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-lg ${stat.bg}`}>
                <stat.icon className={`w-5 h-5 ${stat.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Compliance Rate Banner */}
      <div className="bg-gradient-to-r from-accent-600/20 to-accent-500/5 border border-accent-500/30 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <TrendingUp className="w-6 h-6 text-accent-400" />
          <div>
            <p className="text-white font-medium">Compliance Rate: 97.8%</p>
            <p className="text-sm text-dark-300">Average processing time: 18.5 days (GDPR limit: 30 days)</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-success">5 / 5</p>
          <p className="text-xs text-dark-400">Systems Connected</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-dark-900 border border-dark-700 rounded-xl p-4">
          <h3 className="text-white font-medium mb-4">Request Volume (14 days)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#3f4047" />
              <XAxis dataKey="date" stroke="#7b7d87" fontSize={12} />
              <YAxis stroke="#7b7d87" fontSize={12} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1b1f', border: '1px solid #3f4047', borderRadius: '8px' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="received" fill="#3b82f6" radius={[2, 2, 0, 0]} name="Received" />
              <Bar dataKey="completed" fill="#22c55e" radius={[2, 2, 0, 0]} name="Completed" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-dark-900 border border-dark-700 rounded-xl p-4">
          <h3 className="text-white font-medium mb-4">Data Categories Discovered</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={categoryData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={3}
                dataKey="value"
              >
                {categoryData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1b1f', border: '1px solid #3f4047', borderRadius: '8px' }}
                labelStyle={{ color: '#fff' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-3 mt-2 justify-center">
            {categoryData.map((cat) => (
              <div key={cat.name} className="flex items-center gap-1.5 text-xs text-dark-300">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cat.color }} />
                {cat.name}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Upcoming Deadlines */}
      <div className="bg-dark-900 border border-dark-700 rounded-xl p-4">
        <h3 className="text-white font-medium mb-4 flex items-center gap-2">
          <Clock className="w-4 h-4 text-warning" />
          Upcoming Deadlines
        </h3>
        <div className="space-y-3">
          {upcomingDeadlines.map((item) => (
            <div key={item.ref} className="flex items-center justify-between py-2 border-b border-dark-700 last:border-0">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${
                  item.risk === 'high' ? 'bg-danger' : item.risk === 'medium' ? 'bg-warning' : 'bg-success'
                }`} />
                <div>
                  <p className="text-sm text-white">{item.requester}</p>
                  <p className="text-xs text-dark-400">{item.ref}</p>
                </div>
              </div>
              <div className="text-right">
                <p className={`text-sm font-medium ${
                  item.days <= 5 ? 'text-danger' : item.days <= 10 ? 'text-warning' : 'text-dark-200'
                }`}>
                  {item.days} days remaining
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
