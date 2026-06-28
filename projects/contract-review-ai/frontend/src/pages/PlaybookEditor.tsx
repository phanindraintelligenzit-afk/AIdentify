import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { api } from '../services/api'
import { Playbook, ContractType, ClauseRiskLevel, ClauseRule } from '../types'
import { Button } from '../components/ui/Button'
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Textarea } from '../components/ui/Textarea'
import { Select } from '../components/ui/Select'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { Alert } from '../components/ui/Alert'
import { Plus, Trash2, GripVertical, ChevronDown, ChevronUp, Save, ArrowLeft } from 'lucide-react'

const playbookSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  contract_type: z.enum(['nda', 'msa', 'other']),
  is_default: z.boolean().optional(),
  is_active: z.boolean().optional(),
  rules: z.array(z.object({
    clause_name: z.string().min(1, 'Clause name is required'),
    clause_patterns: z.array(z.string()).optional(),
    required_elements: z.array(z.string()).optional(),
    forbidden_elements: z.array(z.string()).optional(),
    risk_level: z.enum(['high', 'medium', 'low', 'approved']),
    redline_suggestion: z.string().optional(),
    explanation: z.string().optional(),
    is_active: z.boolean().optional(),
    order: z.number().optional(),
  })),
})

type PlaybookForm = z.infer<typeof playbookSchema>

const contractTypes: { value: ContractType; label: string }[] = [
  { value: 'nda', label: 'NDA' },
  { value: 'msa', label: 'MSA' },
  { value: 'other', label: 'Other' },
]

const riskLevels: { value: ClauseRiskLevel; label: string }[] = [
  { value: 'high', label: 'High Risk' },
  { value: 'medium', label: 'Medium Risk' },
  { value: 'low', label: 'Low Risk' },
  { value: 'approved', label: 'Approved' },
]

const defaultClauseNames = [
  'confidentiality', 'term', 'termination', 'liability_cap', 'indemnification',
  'governing_law', 'assignment', 'non_solicit', 'non_compete', 'data_protection',
  'force_majeure', 'dispute_resolution', 'ip_ownership', 'payment_terms', 'warranties',
]

export const PlaybookEditor = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isEditing = !!id
  
  const { data: playbook, isLoading: playbookLoading } = useQuery({
    queryKey: ['playbook', id],
    queryFn: async () => {
      const response = await api.get<Playbook>(`/playbooks/${id}`)
      return response.data
    },
    enabled: isEditing,
  })
  
  const { mutate: savePlaybook, isPending: isSaving } = useMutation({
    mutationFn: async (data: PlaybookForm) => {
      if (isEditing) {
        const response = await api.put<Playbook>(`/playbooks/${id}`, data)
        return response.data
      } else {
        const response = await api.post<Playbook>('/playbooks', data)
        return response.data
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['playbooks'] })
      navigate('/playbooks')
    },
    onError: (error: any) => {
      console.error('Save failed:', error)
    },
  })
  
  const { register, control, handleSubmit, watch, setValue, formState: { errors } } = useForm<PlaybookForm>({
    resolver: zodResolver(playbookSchema),
    defaultValues: {
      name: '',
      description: '',
      contract_type: 'nda',
      is_default: false,
      is_active: true,
      rules: [],
    },
  })
  
  const { fields, append, remove, move } = useFieldArray({ control, name: 'rules' })
  const watchedRules = watch('rules')
  
  useEffect(() => {
    if (isEditing && playbook && watchedRules.length === 0) {
      // Load existing rules
      const rules = (playbook as any).rules || []
      rules.forEach((rule: any, index: number) => {
        append({
          clause_name: rule.clause_name,
          clause_patterns: rule.clause_patterns || [],
          required_elements: rule.required_elements || [],
          forbidden_elements: rule.forbidden_elements || [],
          risk_level: rule.risk_level || 'medium',
          redline_suggestion: rule.redline_suggestion || '',
          explanation: rule.explanation || '',
          is_active: rule.is_active !== false,
          order: rule.order !== undefined ? rule.order : index,
        })
      })
      setValue('name', playbook.name)
      setValue('description', playbook.description || '')
      setValue('contract_type', playbook.contract_type)
      setValue('is_default', playbook.is_default)
      setValue('is_active', playbook.is_active)
    }
  }, [playbook, isEditing, append, setValue, watchedRules.length])
  
  const addRule = () => {
    append({
      clause_name: '',
      clause_patterns: [],
      required_elements: [],
      forbidden_elements: [],
      risk_level: 'medium',
      redline_suggestion: '',
      explanation: '',
      is_active: true,
      order: fields.length,
    })
  }
  
  const onSubmit = (data: PlaybookForm) => {
    savePlaybook(data)
  }
  
  if (isEditing && playbookLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }
  
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{isEditing ? 'Edit Playbook' : 'Create Playbook'}</h1>
          <p className="text-muted-foreground mt-1">Define rules for AI-powered contract review</p>
        </div>
        <Button variant="outline" onClick={() => navigate('/playbooks')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Playbook Details</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <Input
                label="Name"
                placeholder="e.g., Standard NDA Playbook"
                {...register('name')}
                error={errors.name?.message}
              />
              <Select
                label="Contract Type"
                options={contractTypes.map(t => ({ value: t.value, label: t.label }))}
                {...register('contract_type')}
              />
            </div>
            
            <Textarea
              label="Description"
              placeholder="Describe what this playbook covers..."
              {...register('description')}
              rows={3}
            />
            
            <div className="flex items-center gap-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" {...register('is_default')} className="h-4 w-4 rounded border-input" />
                <span className="text-sm">Set as default for this contract type</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" {...register('is_active')} className="h-4 w-4 rounded border-input" />
                <span className="text-sm">Active</span>
              </label>
            </div>
          </form>
        </CardContent>
      </Card>
      
      {/* Rules */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Review Rules</CardTitle>
          <Button variant="secondary" size="sm" onClick={addRule}>
            <Plus className="mr-2 h-4 w-4" />
            Add Rule
          </Button>
        </CardHeader>
        <CardContent>
          {fields.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No rules defined yet. Click "Add Rule" to create your first rule.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {fields.map((field, index) => (
                <RuleField
                  key={field.id}
                  index={index}
                  field={field}
                  fields={fields}
                  register={register}
                  control={control}
                  remove={remove}
                  move={move}
                  errors={errors}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Actions */}
      <div className="flex justify-end gap-4">
        <Button variant="outline" onClick={() => navigate('/playbooks')}>
          Cancel
        </Button>
        <Button type="submit" form="playbook-form" loading={isSaving}>
          <Save className="mr-2 h-4 w-4" />
          {isEditing ? 'Save Changes' : 'Create Playbook'}
        </Button>
      </div>
      
      <form id="playbook-form" onSubmit={handleSubmit(onSubmit)} className="hidden">
        <input type="hidden" name="dummy" />
      </form>
    </div>
  )
}

interface RuleFieldProps {
  index: number
  field: any
  fields: any[]
  register: any
  control: any
  remove: (index: number) => void
  move: (from: number, to: number) => void
  errors: any
}

const RuleField = ({ index, field, fields, register, control, remove, move, errors }: RuleFieldProps) => {
  const [expanded, setExpanded] = useState(true)
  const ruleErrors = errors.rules?.[index]
  
  const clauseNameOptions = defaultClauseNames.map(name => ({
    value: name,
    label: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
  }))
  
  return (
    <Card className={ruleErrors ? 'border-destructive' : ''}>
      <CardHeader className="p-4 cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-3">
          <GripVertical className="h-5 w-5 text-muted-foreground hover:text-foreground" />
          {expanded ? <ChevronDown className="h-5 w-5 text-muted-foreground" /> : <ChevronUp className="h-5 w-5 text-muted-foreground" />}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <Input
                placeholder="Clause name (e.g., confidentiality)"
                {...register(`rules.${index}.clause_name`)}
                error={ruleErrors?.clause_name?.message}
                className="w-auto"
              />
              <Badge variant={ruleErrors?.risk_level ? 'destructive' : riskLevels.find(r => r.value === watch(`rules.${index}.risk_level`))?.value || 'default'}>
                {riskLevels.find(r => r.value === watch(`rules.${index}.risk_level`))?.label || 'Medium Risk'}
              </Badge>
            </div>
            {ruleErrors?.clause_name && (
              <p className="text-sm text-destructive mt-1">{ruleErrors.clause_name.message}</p>
            )}
          </div>
          <Button variant="ghost" size="icon" onClick={(e) => { e.stopPropagation(); remove(index); }}>
            <Trash2 className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      </CardHeader>
      
      {expanded && (
        <CardContent className="space-y-4 pt-0">
          <div className="grid gap-4 md:grid-cols-2">
            <Select
              label="Clause Name"
              options={clauseNameOptions}
              placeholder="Select or type clause name"
              {...register(`rules.${index}.clause_name`)}
            />
            <Select
              label="Risk Level"
              options={riskLevels.map(r => ({ value: r.value, label: r.label }))}
              {...register(`rules.${index}.risk_level`)}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Patterns (one per line)</label>
            <Textarea
              placeholder="confidential\nnon-disclosure\nproprietary information"
              value={watch(`rules.${index}.clause_patterns`)?.join('\n') || ''}
              onChange={(e) => control.setValue(`rules.${index}.clause_patterns`, e.target.value.split('\n').filter(Boolean))}
              rows={3}
            />
          </div>
          
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium mb-2">Required Elements (one per line)</label>
              <Textarea
                placeholder="definition of confidential information\nexceptions\npermitted disclosures"
                value={watch(`rules.${index}.required_elements`)?.join('\n') || ''}
                onChange={(e) => control.setValue(`rules.${index}.required_elements`, e.target.value.split('\n').filter(Boolean))}
                rows={3}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Forbidden Elements (one per line)</label>
              <Textarea
                placeholder="unilateral confidentiality\nperpetual confidentiality without sunset"
                value={watch(`rules.${index}.forbidden_elements`)?.join('\n') || ''}
                onChange={(e) => control.setValue(`rules.${index}.forbidden_elements`, e.target.value.split('\n').filter(Boolean))}
                rows={3}
              />
            </div>
          </div>
          
          <Textarea
            label="Redline Suggestion"
            placeholder="Make confidentiality mutual. Add sunset clause (2-3 years)..."
            {...register(`rules.${index}.redline_suggestion`)}
            rows={3}
          />
          
          <Textarea
            label="Explanation"
            placeholder="NDAs should protect both parties equally. Perpetual confidentiality is rarely enforceable..."
            {...register(`rules.${index}.explanation`)}
            rows={2}
          />
          
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" {...register(`rules.${index}.is_active`)} className="h-4 w-4 rounded border-input" />
              <span className="text-sm">Active rule</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="number" {...register(`rules.${index}.order`, { valueAsNumber: true })} className="w-20 h-8 px-2 border border-input rounded bg-background text-sm" min="0" />
              <span className="text-sm text-muted-foreground">Order</span>
            </label>
          </div>
        </CardContent>
      )}
    </Card>
  )
}

// Need to import watch from useForm
import { useForm } from 'react-hook-form'
const { watch } = useForm<PlaybookForm>()