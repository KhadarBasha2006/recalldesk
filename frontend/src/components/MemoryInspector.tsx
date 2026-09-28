import { useEffect, useState } from 'react'
import { getMentalModels, getStats, searchMemories, seedMemory } from '../api'
import type { BankStats, MentalModel, MemoryItem } from '../types'

export default function MemoryInspector({ refreshKey }: { refreshKey: number }) {
  const [stats, setStats] = useState<BankStats | null>(null)
  const [memories, setMemories] = useState<MemoryItem[]>([])
  const [models, setModels] = useState<MentalModel[]>([])
  const [query, setQuery] = useState('')
  const [seeding, setSeeding] = useState(false)

  async function refresh(q = query) {
    try {
      const [s, mem, mm] = await Promise.all([getStats(), searchMemories(q), getMentalModels()])
      setStats(s)
      setMemories(mem.memories || [])
      setModels(mm.mental_models || [])
    } catch {
      /* backend not up yet */
    }
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey])

  async function handleSeed() {
    setSeeding(true)
    try {
      await seedMemory()
      await refresh()
    } finally {
      setSeeding(false)
    }
  }

  return (
    <div className="w-[380px] shrink-0 border-l border-edge bg-[#0d1329] flex flex-col">
      <div className="px-4 py-3 border-b border-edge">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200">🧠 Memory Inspector</h2>
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="text-[11px] px-2 py-1 rounded-lg bg-violet/20 border border-violet/40 text-violet-200 hover:bg-violet/30 disabled:opacity-50"
          >
            {seeding ? 'seeding…' : 'seed history'}
          </button>
        </div>
        {stats && (
          <div className="grid grid-cols-3 gap-2 mt-3">
            <Stat label="memories" value={stats.memories} />
            <Stat label="observations" value={stats.observations} />
            <Stat label="plays" value={stats.mental_models} />
          </div>
        )}
      </div>

      <div className="px-4 py-2 border-b border-edge">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && refresh()}
          placeholder="Search the bank…"
          className="w-full bg-panel border border-edge rounded-lg px-3 py-2 text-xs outline-none focus:border-violet"
        />
      </div>

      <div className="flex-1 overflow-y-auto chat-scroll px-4 py-3 space-y-2">
        {models.length > 0 && (
          <>
            <div className="text-[11px] uppercase tracking-wide text-slate-400 pt-1">Learned plays · mental models</div>
            {models.map((mm) => (
              <div key={mm.id || mm.name} className="bg-violet/10 border border-violet/30 rounded-xl px-3 py-2">
                <div className="text-xs font-semibold text-violet-200">{mm.name}</div>
                <div className="text-[11px] text-slate-300 mt-1 leading-snug">{mm.text}</div>
              </div>
            ))}
          </>
        )}

        <div className="text-[11px] uppercase tracking-wide text-slate-400 pt-2">Everything the bank knows</div>
        {memories.length === 0 && (
          <div className="text-xs text-slate-500 py-4">
            No memories found. Click “seed history”, then chat — every turn appears here instantly.
          </div>
        )}
        {memories.map((m, i) => (
          <div key={m.id || i} className="bg-panel border border-edge rounded-xl px-3 py-2">
            <div className="flex items-center gap-2 mb-1">
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded-full border ${
                  m.type === 'observation'
                    ? 'bg-violet-900/50 text-violet-200 border-violet-500/40'
                    : m.type === 'experience'
                      ? 'bg-sky-900/50 text-sky-200 border-sky-500/40'
                      : 'bg-emerald-900/50 text-emerald-200 border-emerald-500/40'
                }`}
              >
                {m.type || 'fact'}
              </span>
              {m.created_at && <span className="text-[10px] text-slate-500">{m.created_at.slice(0, 10)}</span>}
            </div>
            <div className="text-[11px] text-slate-300 leading-snug">{m.text}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-panel border border-edge rounded-lg px-2 py-1.5 text-center">
      <div className="text-lg font-bold text-slate-100">{value}</div>
      <div className="text-[10px] text-slate-400 uppercase tracking-wide">{label}</div>
    </div>
  )
}
