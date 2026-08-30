from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse

from app.auth.dependencies import get_current_username
from app.config import Settings, get_settings

router = APIRouter(prefix="/api/v1/documents", tags=["documents"], dependencies=[Depends(get_current_username)])


@router.get("/{filename}/markdown", response_class=PlainTextResponse)
def document_markdown(filename: str, settings: Settings = Depends(get_settings)) -> str:
    """Serves the Markdown rendering of a document - what the Evidence pane shows for a
    citation. No PDF is served: `.stem` also discards any directory component a caller
    might smuggle into `filename`, so this can only ever read out of `markdown_dir`."""
    stem = Path(filename).stem
    path = settings.markdown_dir_path / f"{stem}.md"
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document not found")
    return path.read_text(encoding="utf-8")
