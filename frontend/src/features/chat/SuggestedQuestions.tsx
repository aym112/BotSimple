// SPEC.md section 43 — these buttons only populate the input; they still go through the
// normal query pipeline (no shortcut/lookup table).
const SUGGESTIONS = [
  'What is the current annual dental care limit for POL-2026-0042?',
  'What is the effective date of POL-2026-0042?',
  'Is a visible laptop stolen from a locked unattended car covered under POL-2026-0188?',
  'What is the current water damage deductible for POL-2026-0291?',
  'What is the management fee for ISIN LU1234567896?',
]

export function SuggestedQuestions({ onPick }: { onPick: (question: string) => void }) {
  return (
    <div className="mx-auto max-w-lg py-12 text-center">
      <h2 className="text-lg font-semibold text-slate-800">Ask about a policy or fund</h2>
      <p className="mt-1 text-sm text-slate-500">Try one of these, or type your own question below.</p>
      <div className="mt-6 flex flex-col gap-2">
        {SUGGESTIONS.map((question) => (
          <button
            key={question}
            onClick={() => onPick(question)}
            className="rounded-md border border-slate-200 bg-white px-3 py-2 text-left text-sm text-slate-700 hover:border-slate-400 hover:bg-slate-50"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  )
}
