import { useState } from 'react'
import { ArrowRight, Check } from 'lucide-react'

export default function CreateDSAR() {
  const [step, setStep] = useState(1)
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    type: 'access',
    regulation: 'gdpr',
    description: '',
  })
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = () => {
    setSubmitted(true)
  }

  if (submitted) {
    return (
      <div className="max-w-lg mx-auto mt-12 text-center">
        <div className="w-16 h-16 bg-success/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <Check className="w-8 h-8 text-success" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">DSAR Request Created</h2>
        <p className="text-dark-300 mb-4">
          Reference: <span className="font-mono text-accent-400">DSAR-20260628-0001</span>
        </p>
        <p className="text-sm text-dark-400 mb-6">
          Deadline: 30 days from now (GDPR). The request has been queued for processing.
        </p>
        <button
          onClick={() => { setSubmitted(false); setStep(1); setForm({ name: '', email: '', phone: '', type: 'access', regulation: 'gdpr', description: '' }) }}
          className="px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-500 transition-colors"
        >
          Create Another Request
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">New DSAR Request</h2>
        <p className="text-dark-400 mt-1">Create a new Data Subject Access Request</p>
      </div>

      {/* Progress */}
      <div className="flex items-center gap-2">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step >= s ? 'bg-accent-600 text-white' : 'bg-dark-700 text-dark-400'
            }`}>
              {s}
            </div>
            {s < 3 && <div className={`w-12 h-0.5 ${step > s ? 'bg-accent-600' : 'bg-dark-700'}`} />}
          </div>
        ))}
        <span className="ml-4 text-sm text-dark-400">
          {step === 1 ? 'Requester Info' : step === 2 ? 'Request Details' : 'Review'}
        </span>
      </div>

      <div className="bg-dark-900 border border-dark-700 rounded-xl p-6">
        {step === 1 && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Requester Information</h3>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Full Name *</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-accent-500"
                placeholder="John Doe"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Email Address *</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-accent-500"
                placeholder="john@example.com"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Phone (optional)</label>
              <input
                type="tel"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-accent-500"
                placeholder="+1 234 567 8900"
              />
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Request Details</h3>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Regulation</label>
              <select
                value={form.regulation}
                onChange={(e) => setForm({ ...form, regulation: e.target.value })}
                className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-accent-500"
              >
                <option value="gdpr">GDPR (EU)</option>
                <option value="ccpa">CCPA (California)</option>
                <option value="lgpd">LGPD (Brazil)</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Request Type</label>
              <select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
                className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-accent-500"
              >
                <option value="access">Right of Access (Art. 15)</option>
                <option value="erasure">Right to Erasure (Art. 17)</option>
                <option value="rectification">Right to Rectification (Art. 16)</option>
                <option value="portability">Right to Data Portability (Art. 20)</option>
                <option value="objection">Right to Object (Art. 21)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Description</label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={4}
                className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-white focus:outline-none focus:border-accent-500 resize-none"
                placeholder="Describe the request details..."
              />
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Review & Confirm</h3>
            <div className="bg-dark-800 rounded-lg p-4 space-y-2">
              <div className="flex justify-between">
                <span className="text-dark-400">Name:</span>
                <span className="text-white">{form.name || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-dark-400">Email:</span>
                <span className="text-white">{form.email || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-dark-400">Regulation:</span>
                <span className="text-white uppercase">{form.regulation}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-dark-400">Type:</span>
                <span className="text-white capitalize">{form.type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-dark-400">Deadline:</span>
                <span className="text-white">{form.regulation === 'gdpr' ? '30 days' : '45 days'}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-between">
        <button
          onClick={() => setStep(Math.max(1, step - 1))}
          className={`px-4 py-2 rounded-lg text-sm ${step === 1 ? 'invisible' : 'bg-dark-700 text-dark-200 hover:bg-dark-600'}`}
        >
          Back
        </button>
        {step < 3 ? (
          <button
            onClick={() => setStep(step + 1)}
            className="px-4 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-500 text-sm flex items-center gap-2"
          >
            Next <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            className="px-4 py-2 bg-success text-white rounded-lg hover:bg-success/90 text-sm"
          >
            Create Request
          </button>
        )}
      </div>
    </div>
  )
}
