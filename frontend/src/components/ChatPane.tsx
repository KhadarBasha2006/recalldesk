import { useEffect, useRef } from 'react'
import type { ChatMessage } from '../types'

function MemoryChip({ text, type }: { text: string; type?: string }) {
  const label = (type || 'fact').toLowerCase()
  const color =
    label === 'observation'
      ? 'bg-violet-900/60 text-violet-200 border-violet-500/40'
      : label === 'experience'
        ? 'bg-sky-900/60 text-sky-200 border-sky-500/40'
        : 'bg-emerald-900/60 text-emerald-200 border-emerald-500/40'
  return (
    <span className={`${color} border text-[11px] px-2 py-0.5 rounded-full truncate max-w-[280px] inline-block`} title={text}>
      {text.length > 70 ? text.slice(0, 70) + '…' : text}
    </span>
  )
}

export default function ChatPane({ messages, busy }: { messages: ChatMessage[]; busy: boolean }) {
  const endRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, busy])

  return (
    <div className="flex-1 overflow-y-auto chat-scroll px-6 py-4 space-y-4">
      {messages.map((m, i) => (
        <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
          <div
            className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              m.role === 'user'
                ? 'bg-violet text-white rounded-br-sm'
                : 'bg-panel border border-edge rounded-bl-sm'
            }`}
          >
            <div className="whitespace-pre-wrap">{m.text}</div>

            {m.role === 'assistant' && m.usedMemory === false && (
              <div className="mt-2 text-[11px] text-amber-300/90 border border-amber-500/30 bg-amber-900/20 rounded-lg px-2 py-1 inline-block">
                🚫 memory off — stateless mode
              </div>
            )}

            {m.role === 'assistant' && m.memories && m.memories.length > 0 && (
              <div className="mt-3">
                <div className="text-[11px] uppercase tracking-wide text-slate-400 mb-1">
                  🧠 recalled {m.memories.length} memor{m.memories.length === 1 ? 'y' : 'ies'}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {m.memories.slice(0, 6).map((mem, j) => (
                    <MemoryChip key={j} text={mem.text} type={mem.type} />
                  ))}
                </div>
              </div>
            )}

            {m.role === 'assistant' && m.toolCalls && m.toolCalls.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {m.toolCalls.map((tc, j) => (
                  <span
                    key={j}
                    className="text-[11px] bg-slate-800 border border-edge text-slate-300 px-2 py-0.5 rounded-full"
                    title={JSON.stringify(tc.arguments)}
                  >
                    🔧 {tc.name}
                  </span>
                ))}
              </div>
            )}

            {m.role === 'assistant' && m.latencyMs ? (
              <div className="mt-2 text-[10px] text-slate-500">{m.latencyMs} ms</div>
            ) : null}
          </div>
        </div>
      ))}
      {busy && (
        <div className="flex justify-start">
          <div className="bg-panel border border-edge rounded-2xl px-4 py-3 text-sm text-slate-400 animate-pulse">
            RecallDesk is recalling…
          </div>
        </div>
      )}
      <div ref={endRef} />
    </div>
  )
}
