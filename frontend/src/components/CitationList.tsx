import type { Citation } from '../api/types'

export function citationKey(citation: Citation): string {
  return `${citation.filename}#${citation.page}`
}

export function CitationList({
  citations,
  onSelect,
  selectedId,
}: {
  citations: Citation[]
  onSelect: (citation: Citation) => void
  selectedId: string | null
}) {
  if (citations.length === 0) return null

  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {citations.map((citation) => {
        const key = citationKey(citation)
        return (
          <button
            key={key}
            onClick={() => onSelect(citation)}
            className={`rounded-md border px-2 py-1 text-xs transition-colors ${
              selectedId === key
                ? 'border-slate-900 bg-slate-900 text-white'
                : 'border-slate-300 bg-white text-slate-700 hover:border-slate-500'
            }`}
          >
            {citation.document_title} · p. {citation.page}
            {citation.section_title ? ` · ${citation.section_title}` : ''}
          </button>
        )
      })}
    </div>
  )
}
