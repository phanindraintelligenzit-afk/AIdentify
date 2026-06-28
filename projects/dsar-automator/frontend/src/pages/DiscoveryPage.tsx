import { useState } from 'react'
import { Database, Check, X, AlertTriangle, Server, HardDrive, Cloud, CreditCard, MessageSquare, Megaphone } from 'lucide-react'

const dataSources = [
  { id: 'postgresql', name: 'PostgreSQL Database', type: 'database', status: 'connected', records: 492, icon: Database },
  { id: 'salesforce', name: 'Salesforce CRM', type: 'crm', status: 'connected', records: 28, icon: Server },
  { id: 's3', name: 'AWS S3 Documents', type: 'storage', status: 'connected', records: 12, icon: Cloud },
  { id: 'stripe', name: 'Stripe Payments', type: 'payment', status: 'connected', records: 45, icon: CreditCard },
  { id: 'hubspot', name: 'HubSpot Marketing', type: 'marketing', status: 'available', records: 0, icon: Megaphone },
  { id: 'intercom', name: 'Intercom Chat', type: 'support', status: 'available', records: 0, icon: MessageSquare },
]

const discoveryResults = [
  { source: 'PostgreSQL', category: 'Personal Info', records: 150, pii: true, thirdParty: false },
  { source: 'PostgreSQL', category: 'Transactions', records: 342, pii: false, thirdParty: false },
  { source: 'Salesforce', category: 'Communications', records: 28, pii: true, thirdParty: false },
  { source: 'AWS S3', category: 'Support Tickets', records: 12, pii: true, thirdParty: true },
  { source: 'Stripe', category: 'Financial Data', records: 45, pii: true, thirdParty: false },
]

export default function DiscoveryPage() {
  const [scanning, setScanning] = useState(false)
  const [scanned, setScanned] = useState(true)

  const handleScan = () => {
    setScanning(true)
    setScanned(false)
    setTimeout(() => {
      setScanning(false)
      setScanned(true)
    }, 2000)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Data Discovery</h2>
          <p className="text-dark-400 mt-1">Scan connected systems for personal data</p>
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-500 text-sm disabled:opacity-50"
        >
          {scanning ? 'Scanning...' : 'Run Discovery Scan'}
        </button>
      </div>

      {/* Data Sources */}
      <div className="bg-dark-900 border border-dark-700 rounded-xl p-4">
        <h3 className="text-white font-medium mb-4">Connected Data Sources</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {dataSources.map((source) => (
            <div key={source.id} className="bg-dark-800 rounded-lg p-3 flex items-center gap-3">
              <div className={`p-2 rounded-lg ${source.status === 'connected' ? 'bg-success/10' : 'bg-dark-700'}`}>
                <source.icon className={`w-5 h-5 ${source.status === 'connected' ? 'text-success' : 'text-dark-400'}`} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white truncate">{source.name}</p>
                <p className="text-xs text-dark-400 capitalize">{source.type}</p>
              </div>
              {source.status === 'connected' ? (
                <Check className="w-4 h-4 text-success" />
              ) : (
                <X className="w-4 h-4 text-dark-500" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Discovery Results */}
      {scanned && (
        <div className="bg-dark-900 border border-dark-700 rounded-xl p-4">
          <h3 className="text-white font-medium mb-4">
            Discovery Results — DSAR-20260628-0001
          </h3>
          <div className="space-y-3">
            {discoveryResults.map((result, i) => (
              <div key={i} className="flex items-center justify-between py-3 border-b border-dark-700 last:border-0">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-accent-500" />
                  <div>
                    <p className="text-sm text-white">{result.category}</p>
                    <p className="text-xs text-dark-400">{result.source}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm text-white">{result.records} records</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {result.pii && (
                      <span className="px-2 py-0.5 bg-warning/20 text-warning text-xs rounded-full">PII</span>
                    )}
                    {result.thirdParty && (
                      <span className="px-2 py-0.5 bg-danger/20 text-danger text-xs rounded-full flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" />
                        3rd Party
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-dark-700 flex items-center justify-between">
            <p className="text-sm text-dark-300">
              Total: <span className="text-white font-medium">577 records</span> across 5 systems
            </p>
            <button className="px-3 py-1.5 bg-accent-600 text-white text-sm rounded-lg hover:bg-accent-500">
              Generate Response Package
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
