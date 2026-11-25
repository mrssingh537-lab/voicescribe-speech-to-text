from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    words: Optional[List[Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": round(self.start, 2),
            "end": round(self.end, 2),
            "text": self.text.strip(),
            "speaker": self.speaker,
            "words": self.words
        }


@dataclass
class TranscriptResult:
    text: str
    segments: List[TranscriptSegment]
    language: str
    duration: float
    model_name: str = "whisper-large-v3-turbo"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text.strip(),
            "segments": [seg.to_dict() for seg in self.segments],
            "language": self.language,
            "duration": round(self.duration, 2),
            "model_name": self.model_name
        }


class TranscriptionProvider(ABC):
    """
    Base abstraction interface for transcription providers.
    Allows seamlessly swapping between local offline models (LocalWhisperProvider)
    and future cloud/API providers without modifying higher-level application logic.
    """

    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        desired_language: Optional[str] = None,
        word_timestamps: bool = False
    ) -> TranscriptResult:
        """
        Transcribe an audio file at audio_path.
        :param audio_path: Path to standardized 16kHz mono audio file
        :param language: Optional language code (e.g. 'en', 'hi') or None for auto-detection
        :param desired_language: Optional target language code (e.g. 'en', 'hi', 'es') or None/auto for same as spoken
        :param word_timestamps: Whether to extract word-level timestamps
        :return: TranscriptResult
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Return True if model/provider is initialized and ready for inference."""
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Return provider metadata, model name, device, and status."""
        pass


# ==============================================================================
# Cloud API Transcription Provider (Implemented in api_whisper.py)
# ==============================================================================
# See app.services.providers.api_whisper.ApiTranscriptionProvider for the
# cloud-based OpenAI/Groq Whisper implementation.
