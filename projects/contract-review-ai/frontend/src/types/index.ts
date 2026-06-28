export interface User {
  id: string
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export interface Token {
  access_token: string
  token_type: string
}

export interface TokenData {
  email: string | null
}

export type ContractType = 'nda' | 'msa' | 'other'

export type ContractStatus = 'uploaded' | 'processing' | 'completed' | 'failed'

export type ClauseRiskLevel = 'high' | 'medium' | 'low' | 'approved'

export interface Contract {
  id: string
  filename: string
  original_filename: string
  file_size: number
  content_type: string
  contract_type: ContractType
  status: ContractStatus
  owner_id: string
  playbook_id: string | null
  risk_summary: RiskSummary | null
  redline_docx_path: string | null
  redline_pdf_path: string | null
  error_message: string | null
  processing_time_seconds: number | null
  created_at: string
  updated_at: string
  completed_at: string | null
}

export interface ClauseAnalysisResult {
  clause_name: string
  clause_text: string
  risk_level: ClauseRiskLevel
  issues: string[]
  matched_rules: string[]
  redline_suggestion: string | null
  explanation: string | null
  confidence: number
}

export interface RiskSummary {
  total_clauses: number
  high_risk: number
  medium_risk: number
  low_risk: number
  approved: number
  overall_risk_score: number
  risk_breakdown: Record<string, number>
}

export interface ContractAnalysisResponse {
  contract_id: string
  clause_analysis: ClauseAnalysisResult[]
  risk_summary: RiskSummary
  redline_docx_url: string | null
  redline_pdf_url: string | null
}

export interface UploadResponse {
  contract_id: string
  job_id: string
  message: string
  status: ContractStatus
}

export interface JobStatus {
  job_id: string
  contract_id: string
  status: string
  progress: number
  current_step: string | null
  result: Record<string, any> | null
  error: string | null
}

export interface Playbook {
  id: string
  name: string
  description: string | null
  contract_type: ContractType
  rules: Record<string, any>
  is_default: boolean
  is_active: boolean
  owner_id: string
  created_at: string
  updated_at: string
}

export interface PlaybookWithRules extends Playbook {
  rules: ClauseRule[]
}

export interface ClauseRule {
  id: string
  playbook_id: string
  clause_name: string
  clause_patterns: string[]
  required_elements: string[] | null
  forbidden_elements: string[] | null
  risk_level: ClauseRiskLevel
  redline_suggestion: string | null
  explanation: string | null
  is_active: boolean
  order: number
  created_at: string
  updated_at: string
}

export interface DashboardStats {
  total_contracts: number
  completed: number
  processing: number
  failed: number
  average_risk_score: number
  by_type: Record<string, number>
}

export interface HealthResponse {
  status: string
  version: string
  database: string
  redis: string
}