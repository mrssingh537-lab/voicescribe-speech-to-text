import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime
from app.database import Base


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # "audio", "video", "recording"
    is_diarized = Column(Boolean, default=False, nullable=False)
    language = Column(String(20), default="auto", nullable=False)
    desired_language = Column(String(20), default="auto", nullable=False)
    duration = Column(Float, default=0.0, nullable=False)
    text = Column(Text, nullable=False)
    segments_json = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    model_name = Column(String(100), default="Whisper Turbo (Local)", nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "source_type": self.source_type,
            "is_diarized": self.is_diarized,
            "language": self.language,
            "desired_language": self.desired_language,
            "duration": self.duration,
            "text": self.text,
            "segments_json": self.segments_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "model_name": self.model_name or "Whisper Turbo (Local)",
        }
