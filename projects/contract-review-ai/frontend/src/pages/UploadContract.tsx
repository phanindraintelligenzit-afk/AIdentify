import React, { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { UploadResponse, ContractType } from '../types'
import { Button } from '../components/ui/Button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Progress } from '../components/ui/Progress'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { FileText, CheckCircle, AlertCircle, Loader2, XCircle, Upload as UploadIcon } from 'lucide-react'

export const UploadContract = () => {
  const queryClient = useQueryClient()
  const [contractType, setContractType] = useState<ContractType>('nda')
  const [playbookId, setPlaybookId] = useState<string>('')
  const [uploadProgress, setUploadProgress] = useState<number>(0)
  const [processingStatus, setProcessingStatus] = useState<{ jobId: string; progress: number; step: string } | null>(null)
  
  const { mutate: uploadContract, isPending: isUploading } = useMutation({
    mutationFn: async (formData: FormData) => {
      const response = await api.post<UploadResponse>('/contracts/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            setUploadProgress(progress)
          }
        },
      })
      return response.data
    },
    onSuccess: (data) => {
      setUploadProgress(100)
      setProcessingStatus({ jobId: data.job_id, progress: 0, step: 'queued' })
      // Poll for processing status
      pollJobStatus(data.job_id)
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
    },
    onError: (error: any) => {
      console.error('Upload failed:', error)
      setUploadProgress(0)
    },
  })
  
  const { mutate: pollJobStatus } = useMutation({
    mutationFn: async (jobId: string) => {
      const response = await api.get(`/jobs/${jobId}/status`)
      return response.data
    },
    onSuccess: (data) => {
      if (data) {
        setProcessingStatus({
          jobId: data.job_id,
          progress: data.progress,
          step: data.current_step || 'processing',
        })
        if (data.status === 'running' || data.status === 'pending') {
          // Continue polling
          setTimeout(() => pollJobStatus(data.job_id), 2000)
        } else if (data.status === 'completed') {
          setProcessingStatus({ jobId: data.job_id, progress: 100, step: 'completed' })
          queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] })
          queryClient.invalidateQueries({ queryKey: ['contracts'] })
        } else if (data.status === 'failed') {
          setProcessingStatus({ jobId: data.job_id, progress: 100, step: `failed: ${data.error || 'Unknown error'}` })
        }
      }
    },
  })
  
  const onDrop = (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return
    
    const formData = new FormData()
    formData.append('file', file)
    formData.append('contract_type', contractType)
    if (playbookId) formData.append('playbook_id', playbookId)
    
    setUploadProgress(0)
    setProcessingStatus(null)
    uploadContract(formData)
  }
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50MB
  })
  
  const contractTypes: { value: ContractType; label: string; description: string }[] = [
    { value: 'nda', label: 'NDA', description: 'Non-Disclosure Agreement' },
    { value: 'msa', label: 'MSA', description: 'Master Services Agreement' },
    { value: 'other', label: 'Other', description: 'Other contract type' },
  ]
  
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Upload Contract</h1>
        <p className="text-muted-foreground mt-1">Drag and drop a PDF or DOCX file for AI-powered first-pass review</p>
      </div>
      
      {/* Upload Zone */}
      <Card>
        <CardHeader>
          <CardTitle>Select Contract File</CardTitle>
          <CardDescription>PDF or DOCX up to 50MB</CardDescription>
        </CardHeader>
        <CardContent>
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center transition-colors
              ${isDragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'}
            `}
          >
            <input {...getInputProps()} />
            <UploadIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium">{isDragActive ? 'Drop the file here...' : 'Drag & drop a contract file, or click to browse'}</p>
            <p className="text-sm text-muted-foreground mt-1">PDF, DOCX, DOC • Max 50MB</p>
          </div>
          
          {uploadProgress > 0 && uploadProgress < 100 && (
            <div className="mt-4">
              <div className="flex justify-between text-sm mb-1">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} />
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Options */}
      <Card>
        <CardHeader>
          <CardTitle>Review Options</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-3">Contract Type</label>
            <div className="flex gap-4">
              {contractTypes.map((type) => (
                <label
                  key={type.value}
                  className={`flex-1 p-4 rounded-lg border-2 transition-colors cursor-pointer ${
                    contractType === type.value
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <input
                    type="radio"
                    name="contractType"
                    value={type.value}
                    checked={contractType === type.value}
                    onChange={() => setContractType(type.value)}
                    className="sr-only"
                  />
                  <div className="font-medium">{type.label}</div>
                  <div className="text-sm text-muted-foreground">{type.description}</div>
                </label>
              ))}
            </div>
          </div>
          
          <div>
            <label htmlFor="playbookId" className="block text-sm font-medium mb-2">Playbook (Optional)</label>
            <select
              id="playbookId"
              value={playbookId}
              onChange={(e) => setPlaybookId(e.target.value)}
              className="w-full max-w-md px-3 py-2 border border-input bg-background rounded-md text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="">Use default playbook for contract type</option>
              {/* Playbooks would be loaded from API */}
            </select>
            <p className="text-sm text-muted-foreground mt-1">Select a custom playbook or use the default</p>
          </div>
        </CardContent>
      </Card>
      
      {/* Processing Status */}
      {processingStatus && (
        <Card className={processingStatus.step === 'completed' ? 'border-green-500/50' : processingStatus.step.startsWith('failed') ? 'border-red-500/50' : ''}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {processingStatus.step === 'completed' && <CheckCircle className="h-5 w-5 text-green-500" />}
              {processingStatus.step.startsWith('failed') && <AlertCircle className="h-5 w-5 text-red-500" />}
              {processingStatus.progress < 100 && !processingStatus.step.startsWith('failed') && (
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
              )}
              Processing Contract
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">{processingStatus.step}</span>
                <span>{processingStatus.progress}%</span>
              </div>
              <Progress value={processingStatus.progress} />
              {processingStatus.step === 'completed' && (
                <p className="text-green-500 text-sm">Analysis complete! Redirecting...</p>
              )}
              {processingStatus.step.startsWith('failed') && (
                <p className="text-red-500 text-sm">Processing failed: {processingStatus.step.replace('failed: ', '')}</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Tips */}
      <Card className="border-primary/20 bg-primary/5">
        <CardContent className="pt-6">
          <h3 className="font-medium text-primary mb-3 flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Tips for best results
          </h3>
          <ul className="text-sm text-muted-foreground space-y-2">
            <li className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-green-500" /> Use clear, high-quality PDFs (not scanned images)</li>
            <li className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-green-500" /> NDAs and MSAs work best with our default playbooks</li>
            <li className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-green-500" /> Custom playbooks can be created in the Playbooks section</li>
            <li className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-green-500" /> Results include redlined DOCX and risk summary PDF</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}