import os
import logging
import torch
import whisper
from typing import Optional, Dict, Any, List
from app.config import settings
from app.services.providers.base import (
    TranscriptionProvider,
    TranscriptResult,
    TranscriptSegment
)

logger = logging.getLogger("voicescribe.provider.whisper")


class LocalWhisperProvider(TranscriptionProvider):
    """
    Offline Local Transcription Provider using OpenAI's Whisper Large-v3 Turbo.
    Loads model once into memory and performs chunked transcription with timestamps.
    """

    def __init__(self, model_name: str = "turbo", device_override: str = "auto"):
        self.model_name = model_name
        self.device = self._resolve_device(device_override)
        self.fp16 = (self.device == "cuda")
        self.model: Optional[whisper.Whisper] = None
        self._is_ready: bool = False

        logger.info(
            f"[LocalWhisperProvider] Initializing Whisper model '{self.model_name}' "
            f"on device='{self.device}', fp16={self.fp16}"
        )

    def _resolve_device(self, device_override: str) -> str:
        if device_override and device_override.lower() != "auto":
            return device_override.lower()
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            logger.info(f"[LocalWhisperProvider] CUDA detected: {device_name}")
            return "cuda"
        logger.info("[LocalWhisperProvider] No CUDA device detected; defaulting to CPU.")
        return "cpu"

    def load_model(self):
        """
        Loads the Whisper Large-v3 Turbo model into memory.
        Executed ONCE at server startup.
        """
        if self._is_ready and self.model is not None:
            logger.info("[LocalWhisperProvider] Model is already loaded.")
            return

        logger.info(
            f"[LocalWhisperProvider] Loading '{self.model_name}' weights... "
            f"(Float{'16' if self.fp16 else '32'} on {self.device.upper()})"
        )
        try:
            # whisper.load_model handles caching in ~/.cache/whisper
            self.model = whisper.load_model(self.model_name, device=self.device)
            if self.fp16:
                self.model = self.model.half()
            else:
                self.model = self.model.float()
            self._is_ready = True
            logger.info(f"[LocalWhisperProvider] Model '{self.model_name}' successfully loaded and ready.")
        except Exception as e:
            self._is_ready = False
            logger.error(f"[LocalWhisperProvider] Failed to load Whisper model: {e}", exc_info=True)
            raise e

    def is_ready(self) -> bool:
        return self._is_ready and self.model is not None

    def get_info(self) -> Dict[str, Any]:
        return {
            "provider": "local_whisper",
            "model_name": self.model_name,
            "device": self.device,
            "fp16": self.fp16,
            "ready": self.is_ready()
        }

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        desired_language: Optional[str] = None,
        word_timestamps: bool = False
    ) -> TranscriptResult:
        """
        Transcribes the given audio file using Whisper Large-v3 Turbo.
        Supports arbitrary duration audio via 30s window chunking.
        Handles spoken language and desired target output language.
        """
        if not self.is_ready():
            raise RuntimeError("Whisper model is not loaded or not ready for inference.")

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        spoken_lang = language.strip().lower() if (language and language.strip().lower() != "auto") else None

        # Whisper's primary role is accurate speech transcription in the spoken language
        # (or automatic detection if auto). Language translation to desired_language is
        # handled by the dedicated translation service.
        task = "transcribe"
        whisper_lang = spoken_lang

        logger.info(
            f"[LocalWhisperProvider] Transcribing '{audio_path}' "
            f"(spoken={spoken_lang or 'auto'}, task={task}, whisper_lang={whisper_lang})"
        )

        transcribe_args = {
            "task": task,
            "fp16": self.fp16,
            "word_timestamps": word_timestamps,
            "verbose": False
        }

        if whisper_lang:
            transcribe_args["language"] = whisper_lang

        # Run whisper inference
        result = self.model.transcribe(audio_path, **transcribe_args)

        detected_language = result.get("language", language or "unknown")
        raw_segments = result.get("segments", [])
        full_text = result.get("text", "").strip()

        parsed_segments: List[TranscriptSegment] = []
        for seg in raw_segments:
            seg_words = None
            if word_timestamps and "words" in seg:
                seg_words = [
                    {"word": w.get("word", ""), "start": w.get("start", 0.0), "end": w.get("end", 0.0)}
                    for w in seg.get("words", [])
                ]

            parsed_segments.append(
                TranscriptSegment(
                    start=float(seg.get("start", 0.0)),
                    end=float(seg.get("end", 0.0)),
                    text=seg.get("text", "").strip(),
                    words=seg_words
                )
            )

        # Calculate duration from segments or 0.0
        duration = parsed_segments[-1].end if parsed_segments else 0.0

        return TranscriptResult(
            text=full_text,
            segments=parsed_segments,
            language=detected_language,
            duration=duration,
            model_name="Whisper Turbo (Local)"
        )
