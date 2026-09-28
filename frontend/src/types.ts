export interface MemoryItem {
  id?: string
  text: string
  type?: string
  created_at?: string
  score?: number
}

export interface ToolCall {
  name: string
  arguments: Record<string, unknown>
  result: unknown
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
  memories?: MemoryItem[]
  toolCalls?: ToolCall[]
  latencyMs?: number
  usedMemory?: boolean
}

export interface MentalModel {
  id?: string
  name: string
  text: string
  updated_at?: string
}

export interface BankStats {
  memories: number
  observations: number
  mental_models: number
}

export const CUSTOMERS = [
  { name: 'Priya Sharma', email: 'priya.sharma@fastmail.com', hint: 'Pro plan · 2 failed devices · 1 failed escalation' },
  { name: 'James Okafor', email: 'james.okafor@brightloop.io', hint: 'Enterprise Pro · SLA dispute' },
  { name: 'New customer', email: 'sam.reed@pilotmail.com', hint: 'No history — fresh start' },
]
