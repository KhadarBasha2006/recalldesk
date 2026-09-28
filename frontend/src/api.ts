import type { BankStats, MentalModel, MemoryItem } from './types'

const BASE = import.meta.env.VITE_API_URL || ''

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export async function getHealth(): Promise<{ status: string; hindsight: boolean; model: string }> {
  return json(await fetch(`${BASE}/api/health`))
}

export async function getStats(): Promise<BankStats> {
  return json(await fetch(`${BASE}/api/memory/stats`))
}

export async function searchMemories(q = ''): Promise<{ memories: MemoryItem[] }> {
  return json(await fetch(`${BASE}/api/memory/search?q=${encodeURIComponent(q)}`))
}

export async function getMentalModels(): Promise<{ mental_models: MentalModel[] }> {
  return json(await fetch(`${BASE}/api/memory/mental-models`))
}

export async function seedMemory(): Promise<void> {
  await json(await fetch(`${BASE}/api/memory/seed`, { method: 'POST' }))
}

export interface ChatPayload {
  message: string
  customer_email: string
  customer_name: string
  session_id?: string
  use_memory: boolean
}

export async function sendChat(payload: ChatPayload): Promise<{
  reply: string
  memory_used: MemoryItem[]
  tool_calls: ToolCallPayload[]
  latency_ms: number
  session_id: string
  used_memory: boolean
}> {
  return json(await fetch(`${BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }))
}

export interface ToolCallPayload {
  name: string
  arguments: Record<string, unknown>
  result: unknown
}

export async function sendChatStream(
  payload: ChatPayload,
  onMemories: (m: MemoryItem[]) => void,
  onDelta: (t: string) => void,
  onDone: (info: { tool_calls: ToolCallPayload[]; latency_ms: number; session_id: string }) => void,
): Promise<void> {
  const res = await fetch(`${BASE}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok || !res.body) throw new Error(`${res.status} ${res.statusText}`)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const events = buffer.split('\n\n')
    buffer = events.pop() || ''
    for (const evt of events) {
      for (const line of evt.split('\n')) {
        if (!line.startsWith('data:')) continue
        const raw = line.slice(5).trim()
        if (!raw || raw === '[DONE]') continue
        try {
          const obj = JSON.parse(raw)
          if (obj.type === 'memories') onMemories(obj.memories || [])
          else if (obj.type === 'delta') onDelta(obj.text || '')
          else if (obj.type === 'done')
            onDone({ tool_calls: obj.tool_calls || [], latency_ms: obj.latency_ms || 0, session_id: obj.session_id || '' })
        } catch {
          /* ignore malformed keep-alives */
        }
      }
    }
  }
}
