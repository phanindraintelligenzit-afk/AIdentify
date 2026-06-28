import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import { DashboardStats, Contract } from '../types'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Progress } from '../components/ui/Progress'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { formatRelativeTime, formatFileSize, getRiskColor, getRiskLabel, getStatusColor, getStatusLabel } from '../utils/helpers'
import { AlertCircle, CheckCircle, Clock, FileText, TrendingUp, TrendingDown, Upload } from 'lucide-react'

const icons = { AlertCircle, CheckCircle, Clock, FileText, TrendingUp, TrendingDown, Upload }

export const Dashboard = () => {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get<DashboardStats>('/dashboard/stats')
      return response.data
    },
  })
  
  const { data: contracts, isLoading: contractsLoading } = useQuery({
    queryKey: ['contracts', 'recent'],
    queryFn: async () => {
      const response = await api.get<Contract[]>('/contracts', { params: { limit: 10 } })
      return response.data
    },
  })
  
  if (statsLoading || contractsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }
  
  const statCards = [
    { label: 'Total Contracts', value: stats?.total_contracts || 0, icon: 'FileText', color: 'text-blue-400' },
    { label: 'Completed', value: stats?.completed || 0, icon: 'CheckCircle', color: 'text-green-400' },
    { label: 'Processing', value: stats?.processing || 0, icon: 'Clock', color: 'text-yellow-400' },
    { label: 'Avg Risk Score', value: `${stats?.average_risk_score || 0}/100`, icon: 'TrendingUp', color: 'text-purple-400' },
  ]
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Overview of your contract review pipeline</p>
        </div>
        <Link to="/upload">
          <Button>
            <Upload className="mr-2 h-4 w-4" />
            Upload Contract
          </Button>
        </Link>
      </div>
      
      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                  <p className="text-3xl font-bold mt-1">{stat.value}</p>
                </div>
                <div className={`p-3 rounded-lg bg-primary/10 ${stat.color}`}>
                  <icons[stat.icon as keyof typeof icons] className="h-6 w-6" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {/* Recent Contracts */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Contracts</CardTitle>
        </CardHeader>
        <CardContent>
          {contracts?.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium">No contracts yet</h3>
              <p className="text-muted-foreground mt-1">Upload your first contract to get started</p>
              <Link to="/upload" className="mt-4 inline-block">
                <Button>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload Contract
                </Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-12 gap-4 text-sm font-medium text-muted-foreground px-4 py-2 border-b border-border">
                <div className="col-span-3">Contract</div>
                <div className="col-span-2">Type</div>
                <div className="col-span-2">Status</div>
                <div className="col-span-2">Risk Score</div>
                <div className="col-span-2">Updated</div>
                <div className="col-span-1"></div>
              </div>
              {contracts?.map((contract) => (
                <Link key={contract.id} to={`/contracts/${contract.id}`} className="block">
                  <div className="grid grid-cols-12 gap-4 px-4 py-3 hover:bg-accent/50 rounded-lg transition-colors border border-transparent hover:border-border">
                    <div className="col-span-3 flex items-center gap-3 min-w-0">
                      <div className="p-2 bg-secondary rounded-lg">
                        <FileText className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium truncate">{contract.original_filename}</p>
                        <p className="text-xs text-muted-foreground">{formatFileSize(contract.file_size)}</p>
                      </div>
                    </div>
                    <div className="col-span-2 flex items-center">
                      <Badge variant="outline" className="capitalize">{contract.contract_type}</Badge>
                    </div>
                    <div className="col-span-2 flex items-center">
                      <Badge variant={['completed', 'failed'].includes(contract.status) ? 'default' : 'secondary'} className={getStatusColor(contract.status)}>
                        {getStatusLabel(contract.status)}
                      </Badge>
                    </div>
                    <div className="col-span-2 flex items-center gap-3">
                      <div className="w-32">
                        <Progress value={contract.risk_summary?.overall_risk_score || 0} max={100} className="h-1.5" />
                      </div>
                      <span className="text-sm font-medium {getRiskColor(String(contract.risk_summary?.overall_risk_score || 0))}">
                        {contract.risk_summary?.overall_risk_score || 0}/100
                      </span>
                    </div>
                    <div className="col-span-2 flex items-center text-sm text-muted-foreground">
                      {formatRelativeTime(contract.updated_at)}
                    </div>
                    <div className="col-span-1 flex items-center justify-end">
                      <span className="text-muted-foreground">→</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
        <CardFooter className="border-t border-border">
          <Link to="/contracts" className="text-primary hover:underline text-sm font-medium">
            View all contracts →
          </Link>
        </CardFooter>
      </Card>
    </div>
  )
}