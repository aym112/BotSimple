import { useState } from 'react'
import { useTrace } from '../api/hooks'

// Collapsed by default. Shows the actual tool calls the agent made — real actions,
// not a synthetic pipeline timeline — and never the model's internal reasoning text.
export function TraceDrawer({ requestId }: { requestId: string }) {
  const [open, setOpen] = useState(false)
  const trace = useTrace(open ? requestId : null)

  return (
    <div className="mt-3 border-t border-slate-100 pt-2">
      <button
        onClick={() => setOpen((v) => !v)}
        className="text-xs font-medium text-slate-500 hover:text-slate-800"
      >
        {open ? '▾' : '▸'} How this answer was built
      </button>

      {open && (
        <div className="mt-2 space-y-2 rounded-md bg-slate-50 p-3">
          {trace.isLoading && <p className="text-xs text-slate-400">Loading trace...</p>}
          {trace.data?.tool_calls.length === 0 && (
            <p className="text-xs text-slate-500">The agent answered without calling any tools.</p>
          )}
          {trace.data?.tool_calls.map((call, index) => (
            <div key={index} className="text-xs">
              <div className="font-medium text-slate-700">
                {index + 1}. {call.tool}
                <span className="ml-1 font-normal text-slate-400">
                  ({Object.entries(call.input).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join(', ')})
                </span>
              </div>
              <div className="text-slate-500">{call.output_summary}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
