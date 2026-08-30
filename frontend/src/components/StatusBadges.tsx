import type { QueryResponse } from '../api/types'

// Honest by construction: this reflects one real fact (did the agent cite a source),
// not a synthetic confidence score or a flag the model could set to anything.
export function StatusBadges({ response }: { response: QueryResponse }) {
  const hasCitations = response.citations.length > 0

  return (
    <div className="flex flex-wrap gap-1.5">
      <span
        className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
          hasCitations
            ? 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200'
            : 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200'
        }`}
      >
        {hasCitations ? 'Sourced from documents' : 'No supporting citation found'}
      </span>
    </div>
  )
}
