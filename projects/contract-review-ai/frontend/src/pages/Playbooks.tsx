import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import { Playbook, ContractType } from '../types'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { Alert } from '../components/ui/Alert'
import { Plus, Edit, Trash2, BookOpen, FileText, Settings, ChevronDown, ChevronUp } from 'lucide-react'

const contractTypes: { value: ContractType; label: string }[] = [
  { value: 'nda', label: 'NDA' },
  { value: 'msa', label: 'MSA' },
  { value: 'other', label: 'Other' },
]

export const Playbooks = () => {
  const queryClient = useQueryClient()
  const [filterType, setFilterType] = useState<ContractType | 'all'>('all')
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)
  
  const { data: playbooks, isLoading, error, refetch } = useQuery({
    queryKey: ['playbooks'],
    queryFn: async () => {
      const response = await api.get<Playbook[]>('/playbooks')
      return response.data
    },
  })
  
  const { mutate: deletePlaybook, isPending: isDeleting } = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/playbooks/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['playbooks'] })
      setDeleteConfirm(null)
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Failed to delete playbook')
      setDeleteConfirm(null)
    },
  })
  
  const filteredPlaybooks = playbooks?.filter(p => 
    filterType === 'all' || p.contract_type === filterType
  ) || []
  
  const handleDelete = (id: string) => {
    if (window.confirm('Are you sure you want to delete this playbook? This cannot be undone.')) {
      setDeleteConfirm(id)
      deletePlaybook(id)
    }
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
        Failed to load playbooks. <Button variant="ghost" size="sm" onClick={() => refetch()}>Retry</Button>
      </Alert>
    )
  }
  
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold">Playbooks</h1>
          <p className="text-muted-foreground mt-1">Manage your contract review playbooks and rules</p>
        </div>
        <Link to="/playbooks/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create Playbook
          </Button>
        </Link>
      </div>
      
      {/* Filter */}
      <Card>
        <CardContent className="p-4 pt-6">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium">Filter by type:</label>
            <Select
              value={filterType}
              onValueChange={setFilterType}
              options={[
                { value: 'all', label: 'All Types' },
                ...contractTypes,
              ]}
              className="w-48"
            />
          </div>
        </CardContent>
      </Card>
      
      {/* Playbooks Grid */}
      {filteredPlaybooks.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No playbooks yet</h3>
            <p className="text-muted-foreground mb-6">Create your first playbook to define custom review rules</p>
            <Link to="/playbooks/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Playbook
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredPlaybooks.map((playbook) => (
            <Card key={playbook.id} className={playbook.is_default ? 'border-primary/50 ring-1 ring-primary/20' : ''}>
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold truncate">{playbook.name}</h3>
                      {playbook.is_default && (
                        <Badge variant="default" className="text-xs">Default</Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground truncate">{playbook.description || 'No description'}</p>
                  </div>
                  <Badge variant="outline" className="capitalize whitespace-nowrap shrink-0 ml-2">
                    {playbook.contract_type}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between text-sm text-muted-foreground mb-3">
                  <span>{playbook.rules && typeof playbook.rules === 'object' && 'rules' in playbook.rules ? (playbook.rules as any).rules?.length || 0 : 0} rules</span>
                  <span>Updated {new Date(playbook.updated_at).toLocaleDateString()}</span>
                </div>
              </CardContent>
              <CardFooter className="flex justify-between pt-0">
                <Link to={`/playbooks/${playbook.id}/edit`}>
                  <Button variant="ghost" size="sm">
                    <Edit className="mr-2 h-4 w-4" />
                    Edit
                  </Button>
                </Link>
                {!playbook.is_default && (
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(playbook.id)} disabled={isDeleting === playbook.id}>
                    <Trash2 className="mr-2 h-4 w-4 text-destructive" />
                    Delete
                  </Button>
                )}
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}