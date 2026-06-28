import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return formatDate(dateString)
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export function getRiskColor(risk: string): string {
  switch (risk) {
    case 'high': return 'text-risk-high bg-risk-high/10 border-risk-high/20'
    case 'medium': return 'text-risk-medium bg-risk-medium/10 border-risk-medium/20'
    case 'low': return 'text-risk-low bg-risk-low/10 border-risk-low/20'
    case 'approved': return 'text-risk-approved bg-risk-approved/10 border-risk-approved/20'
    default: return 'text-muted-foreground bg-muted border-border'
  }
}

export function getRiskLabel(risk: string): string {
  switch (risk) {
    case 'high': return 'High Risk'
    case 'medium': return 'Medium Risk'
    case 'low': return 'Low Risk'
    case 'approved': return 'Approved'
    default: return risk
  }
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'completed': return 'text-green-400 bg-green-400/10 border-green-400/20'
    case 'processing': return 'text-blue-400 bg-blue-400/10 border-blue-400/20'
    case 'uploaded': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20'
    case 'failed': return 'text-red-400 bg-red-400/10 border-red-400/20'
    default: return 'text-muted-foreground bg-muted border-border'
  }
}

export function getStatusLabel(status: string): string {
  switch (status) {
    case 'completed': return 'Completed'
    case 'processing': return 'Processing'
    case 'uploaded': return 'Uploaded'
    case 'failed': return 'Failed'
    default: return status
  }
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str
  return str.slice(0, length) + '...'
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}