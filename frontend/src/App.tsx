import { useEffect, useRef, useState } from 'react'
import ChatPane from './components/ChatPane'
import MemoryInspector from './components/MemoryInspector'
import { getHealth, sendChat, sendChatStream } from './api'
import { CUSTOMERS, type ChatMessage, type MemoryItem } from './types'

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      text:
        "Hi! I'm RecallDesk, Acme Cloud's support agent. Pick a customer on the left and ask me anything — " +
        'I remember every ticket, order and promise this customer has ever made with us. Try: "my router keeps dropping every night" ' +
        '— then toggle Memory OFF and ask again to see the difference.',
      usedMemory: true,
    },
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [useMemory, setUseMemory] = useState(true)
  const [customerIdx, setCustomerIdx] = useState(0)
  const [sessionId, setSessionId] = useState<string | undefined>(undefined)
  const [refreshKey, setRefreshKey] = useState(0)
  const [backendOk, setBackendOk] = useState<boolean | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const customer = CUSTOMERS[customerIdx]

  useEffect(() => {
    getHealth()
      .then((h) => setBackendOk(h.hindsight && h.status === 'ok'))
      .catch(() => setBackendOk(false))
  }, [])

  function push(m: ChatMessage) {
    setMessages((prev) => [...prev, m])
  }

  async function handleSend(text?: string) {
    const message = (text ?? input).trim()
    if (!message || busy) return
    setInput('')
    push({ role: 'user', text: message })
    setBusy(true)
    setMessages((prev) => [...prev.slice(0, -1), { ...prev[prev.length - 1] }])

    const onMemories = (memories: MemoryItem[]) => {
      setMessages((prev) => {
        const next = [...prev]
        next.push({ role: 'assistant', text: '', memories, usedMemory: useMemory })
        return next
      })
    }

    let streamed = ''
    try {
      await sendChatStream(
        {
          message,
          customer_email: customer.email,
          customer_name: customer.name,
          session_id: sessionId,
          use_memory: useMemory,
        },
        onMemories,
        (delta) => {
          streamed += delta
          setMessages((prev) => {
            const next = [...prev]
            const last = next[next.length - 1]
            if (last && last.role === 'assistant') last.text = streamed
            return next
          })
        },
        (info) => {
          setSessionId(info.session_id)
          setRefreshKey((k) => k + 1)
          setMessages((prev) => {
            const next = [...prev]
            const last = next[next.length - 1]
            if (last && last.role === 'assistant') {
              last.toolCalls = info.tool_calls
              last.latencyMs = info.latency_ms
            }
            return next
          })
          setBusy(false)
        },
      )
    } catch {
      // SSE failed — fall back to the non-streaming endpoint.
      try {
        const res = await sendChat({
          message,
          customer_email: customer.email,
          customer_name: customer.name,
          session_id: sessionId,
          use_memory: useMemory,
        })
        push({
          role: 'assistant',
          text: res.reply,
          memories: res.memory_used,
          toolCalls: res.tool_calls,
          latencyMs: res.latency_ms,
          usedMemory: res.used_memory,
        })
        setSessionId(res.session_id)
        setRefreshKey((k) => k + 1)
      } catch (err) {
        push({ role: 'assistant', text: `⚠️ Backend unreachable: ${String(err)}`, usedMemory: useMemory })
      }
    } finally {
      setBusy(false)
      inputRef.current?.focus()
    }
  }

  const SUGGESTIONS = [
    'My router keeps dropping every night again',
    'Where is my refund?',
    "I want to cancel — I've had enough",
  ]

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <header className="border-b border-edge px-6 py-3 flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          <div>
            <div className="font-bold tracking-tight text-slate-100">RecallDesk</div>
            <div className="text-[11px] text-slate-400 -mt-0.5">support agent with total recall · Hindsight memory</div>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <span
            className={`text-[11px] px-2 py-1 rounded-full border ${
              backendOk === null
                ? 'border-slate-600 text-slate-400'
                : backendOk
                  ? 'border-emerald-500/40 text-emerald-300 bg-emerald-900/20'
                  : 'border-red-500/40 text-red-300 bg-red-900/20'
            }`}
          >
            {backendOk === null ? 'checking…' : backendOk ? '● hindsight connected' : '● hindsight offline'}
          </span>
          <button
            onClick={() => setUseMemory((v) => !v)}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition ${
              useMemory
                ? 'bg-violet/25 border-violet/50 text-violet-100'
                : 'bg-slate-800 border-slate-600 text-slate-400'
            }`}
          >
            {useMemory ? '🧠 Memory ON' : '🚫 Memory OFF'}
          </button>
        </div>
      </header>

      <div className="flex-1 flex min-h-0">
        {/* Customers rail */}
        <aside className="w-[260px] shrink-0 border-r border-edge bg-[#0d1329] p-4 space-y-2">
          <div className="text-[11px] uppercase tracking-wide text-slate-400 mb-2">Acting as customer</div>
          {CUSTOMERS.map((c, i) => (
            <button
              key={c.email}
              onClick={() => {
                setCustomerIdx(i)
                setSessionId(undefined)
                setMessages([
                  {
                    role: 'assistant',
                    text: `Now helping ${c.name}. ${c.hint}. Ask me anything — I already know the history.`,
                    usedMemory: true,
                  },
                ])
              }}
              className={`w-full text-left rounded-xl border px-3 py-2.5 transition ${
                i === customerIdx ? 'border-violet bg-violet/15' : 'border-edge bg-panel hover:border-violet/40'
              }`}
            >
              <div className="text-sm font-medium text-slate-100">{c.name}</div>
              <div className="text-[11px] text-slate-400 mt-0.5">{c.hint}</div>
            </button>
          ))}

          <div className="pt-4 text-[11px] uppercase tracking-wide text-slate-400">Try asking</div>
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => handleSend(s)}
              disabled={busy}
              className="w-full text-left text-xs rounded-lg border border-edge bg-panel px-3 py-2 text-slate-300 hover:border-violet/40 disabled:opacity-40"
            >
              “{s}”
            </button>
          ))}

          <div className="pt-4 text-[10px] leading-relaxed text-slate-500">
            Powered by <span className="text-slate-400">Hindsight</span> retain · recall · reflect on Groq{' '}
            <span className="text-slate-400">openai/gpt-oss-120b</span>.
          </div>
        </aside>

        {/* Chat */}
        <main className="flex-1 flex flex-col min-w-0">
          <ChatPane messages={messages} busy={busy} />
          <div className="border-t border-edge px-6 py-3">
            <div className="flex gap-2">
              <input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder={useMemory ? 'Ask anything — I remember…' : 'Memory is OFF — I will pretend to meet you for the first time…'}
                className="flex-1 bg-panel border border-edge rounded-xl px-4 py-2.5 text-sm outline-none focus:border-violet"
              />
              <button
                onClick={() => handleSend()}
                disabled={busy || !input.trim()}
                className="px-5 py-2.5 rounded-xl bg-violet text-white text-sm font-semibold hover:bg-violet-600 disabled:opacity-40"
              >
                Send
              </button>
            </div>
          </div>
        </main>

        {/* Inspector */}
        <MemoryInspector refreshKey={refreshKey} />
      </div>
    </div>
  )
}
