import { useDocumentMarkdown } from '../../api/hooks'
import type { Citation } from '../../api/types'

const PAGE_MARKER = /\*\(page (\d+)\)\*/g

// Splits the rendered Markdown (written with a "*(page N)*" marker before each page's
// content - see markdown_writer.py) into per-page text, so the pane can show just the
// page a citation points to instead of dumping the whole document.
function extractPage(markdown: string, page: number): string | null {
  const markers: { page: number; start: number; end: number }[] = []
  let match: RegExpExecArray | null
  PAGE_MARKER.lastIndex = 0
  while ((match = PAGE_MARKER.exec(markdown)) !== null) {
    markers.push({ page: Number(match[1]), start: match.index, end: match.index + match[0].length })
  }

  for (let i = 0; i < markers.length; i++) {
    if (markers[i].page !== page) continue
    const sliceEnd = i + 1 < markers.length ? markers[i + 1].start : markdown.length
    return markdown.slice(markers[i].end, sliceEnd).trim()
  }
  return null
}

export function EvidencePane({ citation }: { citation: Citation | null }) {
  const markdown = useDocumentMarkdown(citation?.filename ?? null)

  if (!citation) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center text-sm text-slate-400">
        Select a citation to view the source text.
      </div>
    )
  }

  const pageText = markdown.data ? extractPage(markdown.data, citation.page) : null

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-200 bg-white px-4 py-2.5">
        <p className="text-sm font-medium text-slate-800">
          {citation.document_title} · p. {citation.page}
        </p>
        {citation.section_title && <p className="text-xs text-slate-500">{citation.section_title}</p>}
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {markdown.isLoading && <p className="text-sm text-slate-400">Loading...</p>}
        {markdown.isError && <p className="text-sm text-red-600">Could not load this document.</p>}
        {markdown.data && pageText === null && (
          <p className="text-sm text-slate-400">Page {citation.page} not found in this document.</p>
        )}
        {pageText !== null && (
          <pre className="whitespace-pre-wrap font-sans text-sm text-slate-800">{pageText}</pre>
        )}
      </div>
    </div>
  )
}
