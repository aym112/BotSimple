import { useState } from 'react'
import { useSubmitQuery } from '../../api/hooks'
import { ApiError } from '../../api/client'
import { citationKey } from '../../components/CitationList'
import type { Citation, Turn } from '../../api/types'
import { EvidencePane } from '../evidence/EvidencePane'
import { AnswerCard } from './AnswerCard'
import { SuggestedQuestions } from './SuggestedQuestions'

export function ChatPage() {
  const [turns, setTurns] = useState<Turn[]>([])
  const [input, setInput] = useState('')
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const submitQuery = useSubmitQuery()

  function ask(question: string) {
    const trimmed = question.trim()
    if (!trimmed || submitQuery.isPending) return

    const turnId = crypto.randomUUID()
    setTurns((prev) => [...prev, { id: turnId, question: trimmed, response: null, error: null }])
    setInput('')

    submitQuery.mutate(trimmed, {
      onSuccess: (response) => {
        setTurns((prev) => prev.map((t) => (t.id === turnId ? { ...t, response } : t)))
        const firstCitation = response.citations[0]
        if (firstCitation) setSelectedCitation(firstCitation)
      },
      onError: (err) => {
        const message = err instanceof ApiError ? err.message : 'Something went wrong'
        setTurns((prev) => prev.map((t) => (t.id === turnId ? { ...t, error: message } : t)))
      },
    })
  }

  return (
    <div className="grid flex-1 grid-cols-1 overflow-hidden md:grid-cols-2">
      <div className="flex flex-col overflow-hidden border-r border-slate-200">
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {turns.length === 0 ? (
            <SuggestedQuestions onPick={ask} />
          ) : (
            <div className="mx-auto max-w-2xl space-y-4">
              {turns.map((turn) => (
                <div key={turn.id}>
                  <p className="mb-2 text-sm font-medium text-slate-800">{turn.question}</p>
                  {turn.error && (
                    <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                      {turn.error}
                    </p>
                  )}
                  {turn.response && (
                    <AnswerCard
                      response={turn.response}
                      onSelectCitation={setSelectedCitation}
                      selectedCitationId={selectedCitation ? citationKey(selectedCitation) : null}
                    />
                  )}
                  {!turn.response && !turn.error && (
                    <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-400">
                      Thinking...
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault()
            ask(input)
          }}
          className="flex items-center gap-2 border-t border-slate-200 bg-white px-4 py-3"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about a policy or fund..."
            className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={submitQuery.isPending}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>

      <div className="hidden flex-col overflow-hidden bg-white md:flex">
        <div className="border-b border-slate-200 px-4 py-2.5">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Evidence</p>
          <p className="text-xs text-slate-400">
            The source PDF behind the highlighted citation, opened at the right page.
          </p>
        </div>
        <div className="flex-1 overflow-hidden">
          <EvidencePane citation={selectedCitation} />
        </div>
      </div>
    </div>
  )
}
