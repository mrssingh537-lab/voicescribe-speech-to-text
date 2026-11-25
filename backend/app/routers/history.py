import json
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Transcript
from app.schemas import TranscriptResponse, TranscriptListItem, SegmentSchema
from app.services.exporters import export_txt, export_srt

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=List[TranscriptListItem])
def list_history(
    search: Optional[str] = Query(None, description="Search in filenames or transcript content"),
    db: Session = Depends(get_db)
):
    """
    Returns list of past transcripts ordered newest first with optional search filter.
    """
    query = db.query(Transcript)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter((Transcript.filename.ilike(term)) | (Transcript.text.ilike(term)))

    transcripts = query.order_by(Transcript.created_at.desc()).all()

    items = []
    for t in transcripts:
        preview = t.text[:140] + ("..." if len(t.text) > 140 else "")
        items.append(
            TranscriptListItem(
                id=t.id,
                filename=t.filename,
                source_type=t.source_type,
                is_diarized=t.is_diarized,
                language=t.language,
                desired_language=getattr(t, "desired_language", "auto") or "auto",
                duration=t.duration,
                text_preview=preview,
                created_at=t.created_at,
                model_name=getattr(t, "model_name", None) or "Whisper Turbo (Local)"
            )
        )
    return items


@router.get("/{transcript_id}", response_model=TranscriptResponse)
def get_history_detail(transcript_id: int, db: Session = Depends(get_db)):
    """
    Fetches full transcript details with individual timestamped segments.
    """
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")

    try:
        segments_raw = json.loads(transcript.segments_json) if transcript.segments_json else []
    except Exception:
        segments_raw = []

    segments = [SegmentSchema(**seg) for seg in segments_raw]

    return TranscriptResponse(
        id=transcript.id,
        filename=transcript.filename,
        source_type=transcript.source_type,
        is_diarized=transcript.is_diarized,
        language=transcript.language,
        desired_language=getattr(transcript, "desired_language", "auto") or "auto",
        duration=transcript.duration,
        text=transcript.text,
        segments=segments,
        created_at=transcript.created_at,
        model_name=getattr(transcript, "model_name", None) or "Whisper Turbo (Local)"
    )


@router.delete("/{transcript_id}")
def delete_history_item(transcript_id: int, db: Session = Depends(get_db)):
    """
    Deletes a transcript record from history.
    """
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")

    db.delete(transcript)
    db.commit()
    return {"success": True, "message": f"Transcript {transcript_id} deleted."}


@router.get("/{transcript_id}/download")
def download_transcript(
    transcript_id: int,
    format: str = Query("txt", pattern="^(txt|srt)$"),
    db: Session = Depends(get_db)
):
    """
    Exports and downloads a transcript as either plain text (.txt) or SubRip subtitles (.srt).
    """
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")

    base_name = re.sub(r"[^\w\-_.]", "_", transcript.filename)
    if "." in base_name:
        base_name = base_name.rsplit(".", 1)[0]

    if format == "srt":
        content = export_srt(transcript)
        filename = f"{base_name}_transcript.srt"
        media_type = "application/x-subrip; charset=utf-8"
    else:
        content = export_txt(transcript)
        filename = f"{base_name}_transcript.txt"
        media_type = "text/plain; charset=utf-8"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
