from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import QueryRequest


def save_query_request(session: Session, question: str, answer_json: dict, tool_calls_json: list) -> QueryRequest:
    record = QueryRequest(question=question, answer_json=answer_json, tool_calls_json=tool_calls_json)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_query_request(session: Session, request_id: UUID) -> QueryRequest | None:
    return session.get(QueryRequest, request_id)
