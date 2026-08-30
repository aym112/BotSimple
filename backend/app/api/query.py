"""POST /api/v1/query - a real LLM agent with tools, not a deterministic pipeline."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_username
from app.db.repositories.query_requests import save_query_request
from app.db.session import get_db
from app.rag.agent import run_agent_query
from app.rag.schemas import Citation, ToolCallRecord

router = APIRouter(prefix="/api/v1", tags=["query"], dependencies=[Depends(get_current_username)])


class QueryRequestBody(BaseModel):
    question: str


class QueryResponse(BaseModel):
    request_id: str
    answer: str
    citations: list[Citation]
    tool_calls: list[ToolCallRecord]


@router.post("/query", response_model=QueryResponse)
def submit_query(body: QueryRequestBody, session: Session = Depends(get_db)) -> QueryResponse:
    result = run_agent_query(body.question)

    record = save_query_request(
        session,
        question=body.question,
        answer_json=result.model_dump(mode="json"),
        tool_calls_json=[t.model_dump(mode="json") for t in result.tool_calls],
    )

    return QueryResponse(
        request_id=str(record.id),
        answer=result.answer,
        citations=result.citations,
        tool_calls=result.tool_calls,
    )
