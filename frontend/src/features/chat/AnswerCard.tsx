import { CitationList } from '../../components/CitationList'
import { StatusBadges } from '../../components/StatusBadges'
import { TraceDrawer } from '../../components/TraceDrawer'
import type { Citation, QueryResponse } from '../../api/types'

export function AnswerCard({
  response,
  onSelectCitation,
  selectedCitationId,
}: {
  response: QueryResponse
  onSelectCitation: (citation: Citation) => void
  selectedCitationId: string | null
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <StatusBadges response={response} />

      <div className="mt-3">
        <p className="whitespace-pre-wrap text-base text-slate-900">{response.answer}</p>
        <CitationList
          citations={response.citations}
          onSelect={onSelectCitation}
          selectedId={selectedCitationId}
        />
      </div>

      <TraceDrawer requestId={response.request_id} />
    </div>
  )
}
