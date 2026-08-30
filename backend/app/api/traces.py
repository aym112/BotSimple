from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_username
from app.db.repositories.query_requests import get_query_request
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/requests", tags=["trace"], dependencies=[Depends(get_current_username)])


@router.get("/{request_id}")
def get_request(request_id: UUID, session: Session = Depends(get_db)) -> dict:
    record = get_query_request(session, request_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Request not found")
    return {
        "request_id": str(record.id),
        "question": record.question,
        "answer": record.answer_json,
        "created_at": record.created_at.isoformat(),
    }


@router.get("/{request_id}/trace")
def get_trace(request_id: UUID, session: Session = Depends(get_db)) -> dict:
    record = get_query_request(session, request_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Request not found")
    return {"request_id": str(record.id), "tool_calls": record.tool_calls_json}
