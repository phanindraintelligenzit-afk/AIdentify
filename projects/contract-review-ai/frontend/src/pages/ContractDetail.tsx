import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../services/api'
import { ContractAnalysisResponse, ClauseAnalysisResult, ClauseRiskLevel } from '../types'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Progress } from '../components/ui/Progress'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { Alert } from '../components/ui/Alert'
import { formatRelativeTime, getRiskColor, getRiskLabel } from '../utils/helpers'
import { Download, FileText, AlertCircle, CheckCircle, ChevronDown, ChevronUp, X } from 'lucide-react'

const riskIcons: Record<ClauseRiskLevel, React.ComponentType<{ className?: string }>> = {
  high: AlertCircle,
  medium: AlertCircle,
  low: CheckCircle,
  approved: CheckCircle,
}

export const ContractDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [expandedClauses, setExpandedClauses] = useState<Set<string>>(new Set())
  
  const { data: analysis, isLoading, error, refetch } = useQuery({
    queryKey: ['contract-analysis', id],
    queryFn: async () => {
      const response = await api.get<ContractAnalysisResponse>(`/contracts/${id}/analysis`)
      return response.data
    },
    enabled: !!id,
  })
  
  const { data: contract } = useQuery({
    queryKey: ['contract', id],
    queryFn: async () => {
      const response = await api.get(`/contracts/${id}`)
      return response.data
    },
    enabled: !!id,
  })
  
  const handleDownload = async (type: 'docx' | 'pdf') => {
    try {
      const response = await api.get(`/contracts/${id}/download/${type}`, {
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${contract?.original_filename || 'contract'}_redlined.${type}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      console.error('Download failed:', err)
    }
  }
  
  const toggleClause = (clauseName: string) => {
    setExpandedClauses(prev => {
      const next = new Set(prev)
      if (next.has(clauseName)) {
        next.delete(clauseName)
      } else {
        next.add(clauseName)
      }
      return next
    })
  }
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }
  
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <div>Failed to load contract analysis. <Button variant="ghost" size="sm" onClick={() => refetch()}>Retry</Button></div>
      </Alert>
    )
  }
  
  if (!analysis) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <div>Contract analysis not found.</div>
      </Alert>
    )
  }
  
  const riskSummary = analysis.risk_summary
  const overallScore = riskSummary?.overall_risk_score || 0
  
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold">{contract?.original_filename || 'Contract Analysis'}</h1>
          <p className="text-muted-foreground mt-1">
            {contract?.contract_type?.toUpperCase() || 'Contract'} • {formatRelativeTime(contract?.updated_at || '')}
            {contract?.status && (
              <>
                <span className="mx-2">•</span>
                <Badge variant={['completed', 'failed'].includes(contract.status) ? 'default' : 'secondary'} className="capitalize">
                  {contract.status}
                </Badge>
              </>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          {analysis.redline_docx_url && (
            <Button variant="outline" onClick={() => handleDownload('docx')}>
              <FileText className="mr-2 h-4 w-4" />
              Download DOCX
            </Button>
          )}
          {analysis.redline_pdf_url && (
            <Button variant="outline" onClick={() => handleDownload('pdf')}>
              <Download className="mr-2 h-4 w-4" />
              Download PDF
            </Button>
          )}
          <Button variant="outline" onClick={() => navigate('/dashboard')}>
            Back to Dashboard
          </Button>
        </div>
      </div>
      
      {/* Risk Summary Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <p className="text-4xl font-bold text-primary">{overallScore}</p>
              <p className="text-sm text-muted-foreground">Overall Risk Score</p>
              <Progress value={overallScore} max={100} className="mt-2 h-2" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-3xl font-bold text-red-500">{riskSummary?.high_risk || 0}</div>
            <p className="text-sm text-muted-foreground">High Risk</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-3xl font-bold text-yellow-500">{riskSummary?.medium_risk || 0}</div>
            <p className="text-sm text-muted-foreground">Medium Risk</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-3xl font-bold text-green-500">{riskSummary?.approved || 0}</div>
            <p className="text-sm text-muted-foreground">Approved</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6 text-center">
            <div className="text-3xl font-bold text-blue-500">{riskSummary?.total_clauses || 0}</div>
            <p className="text-sm text-muted-foreground">Total Clauses</p>
          </CardContent>
        </Card>
      </div>
      
      {/* Clause Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Clause-by-Clause Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          {analysis.clause_analysis.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4" />
              <p>No clauses detected in this contract</p>
            </div>
          ) : (
            <div className="space-y-4">
              {analysis.clause_analysis.map((clause, index) => {
                const Icon = riskIcons[clause.risk_level]
                const isExpanded = expandedClauses.has(clause.clause_name)
                
                return (
                  <div key={`${index}-${clause.clause_name}`} className="border border-border rounded-lg overflow-hidden">
                    <button
                      onClick={() => toggleClause(clause.clause_name)}
                      className="w-full p-4 flex items-center gap-4 hover:bg-accent/50 transition-colors text-left"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3">
                          <span className={`font-medium capitalize ${getRiskColor(clause.risk_level)}`}>
                            {clause.clause_name.replace(/_/g, ' ')}
                          </span>
                          <Badge variant={clause.risk_level === 'high' ? 'destructive' : clause.risk_level === 'medium' ? 'warning' : clause.risk_level === 'approved' ? 'success' : 'default'}>
                            {getRiskLabel(clause.risk_level)}
                          </Badge>
                          <span className="text-sm text-muted-foreground">({Math.round(clause.confidence * 100)}% confidence)</span>
                        </div>
                        {clause.clause_text && (
                          <p className="text-sm text-muted-foreground mt-1 truncate max-w-2xl">
                            {clause.clause_text.slice(0, 200)}...
                          </p>
                        )}
                      </div>
                      {isExpanded ? <ChevronUp className="h-5 w-5 text-muted-foreground" /> : <ChevronDown className="h-5 w-5 text-muted-foreground" />}
                    </button>
                    
                    {isExpanded && (
                      <div className="p-4 border-t border-border bg-muted/30 space-y-4">
                        {clause.clause_text && (
                          <div>
                            <h4 className="font-medium mb-2">Original Clause Text</h4>
                            <pre className="bg-background p-4 rounded-md text-sm overflow-x-auto max-h-64 font-mono">
                              {clause.clause_text}
                            </pre>
                          </div>
                        )}
                        
                        {clause.issues.length > 0 && (
                          <div>
                            <h4 className="font-medium mb-2 flex items-center gap-2 text-destructive">
                              <AlertCircle className="h-4 w-4" />
                              Issues Found
                            </h4>
                            <ul className="space-y-1 list-disc list-inside text-sm text-muted-foreground">
                              {clause.issues.map((issue, i) => (
                                <li key={i}>{issue}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        
                        {clause.redline_suggestion && (
                          <div>
                            <h4 className="font-medium mb-2 flex items-center gap-2 text-primary">
                              <FileText className="h-4 w-4" />
                              Suggested Redline
                            </h4>
                            <div className="bg-background p-4 rounded-md border border-primary/20 text-sm">
                              {clause.redline_suggestion}
                            </div>
                          </div>
                        )}
                        
                        {clause.explanation && (
                          <div>
                            <h4 className="font-medium mb-2">Analysis</h4>
                            <p className="text-sm text-muted-foreground">{clause.explanation}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}