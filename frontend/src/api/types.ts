export interface Citation {
  filename: string
  document_title: string
  page: number
  section_title: string | null
}

export interface ToolCallRecord {
  tool: string
  input: Record<string, unknown>
  output_summary: string
}

export interface QueryResponse {
  request_id: string
  answer: string
  citations: Citation[]
  tool_calls: ToolCallRecord[]
}

export interface TraceResponse {
  request_id: string
  tool_calls: ToolCallRecord[]
}

export interface Turn {
  id: string
  question: string
  response: QueryResponse | null
  error: string | null
}
