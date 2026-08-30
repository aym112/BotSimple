"""Typed contract for the agent's response — deliberately small. The agent (an LLM with
tools) produces free-form text; the only structure we impose is what the UI needs:
the answer, the sources it actually used, and a readable trace of tool calls."""

from pydantic import BaseModel


class Citation(BaseModel):
    filename: str
    document_title: str
    page: int
    section_title: str | None = None


class ToolCallRecord(BaseModel):
    tool: str
    input: dict
    output_summary: str


class StructuredAnswer(BaseModel):
    """What the LLM itself produces (LangGraph's `response_format`). `tool_calls` is
    reconstructed separately from the graph's message history, never asked of the model."""

    answer: str
    citations: list[Citation]


class AgentAnswer(BaseModel):
    answer: str
    citations: list[Citation]
    tool_calls: list[ToolCallRecord]
