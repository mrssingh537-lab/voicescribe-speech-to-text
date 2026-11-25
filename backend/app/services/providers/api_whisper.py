import os
import re
import json
import logging
import subprocess
from typing import Optional, Dict, Any, List
import httpx

from app.services.providers.base import (
    TranscriptionProvider,
    TranscriptResult,
    TranscriptSegment
)

logger = logging.getLogger("voicescribe.provider.api")

# Models known to NOT support verbose_json (require 'json' or 'text')
NON_VERBOSE_MODELS = {
    "gpt-transcribe",
    "gpt-4o-audio-preview",
    "gpt-4o-mini-audio-preview",
}


def get_audio_file_duration(audio_path: str) -> float:
    """Accurately calculates audio duration in seconds from local audio file."""
    if not audio_path or not os.path.exists(audio_path):
        return 0.0
    try:
        import soundfile as sf
        info = sf.info(audio_path)
        if info.duration > 0:
            return float(info.duration)
    except Exception:
        pass
    try:
        import wave
        with wave.open(audio_path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate > 0:
                return float(frames) / float(rate)
    except Exception:
        pass
    try:
        import librosa
        dur = librosa.get_duration(path=audio_path)
        if dur > 0:
            return float(dur)
    except Exception:
        pass
    return 0.0


def build_fallback_segments(full_text: str, duration: float) -> List[TranscriptSegment]:
    """
    Constructs logical timestamped segments when the cloud model/format returns
    raw text or plain JSON without segment timestamps (e.g. gpt-transcribe).
    """
    cleaned_text = (full_text or "").strip()
    if not cleaned_text:
        return []

    # Split into sentences on common punctuation marks followed by whitespace
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned_text) if s.strip()]
    if not sentences:
        sentences = [cleaned_text]

    # If duration is missing, estimate ~0.35s per word with a 1.0s floor
    if duration <= 0.0:
        word_count = max(1, len(cleaned_text.split()))
        duration = round(word_count * 0.35, 2)
    duration = max(duration, 0.5)

    total_chars = sum(len(s) for s in sentences) or 1
    segments: List[TranscriptSegment] = []
    current_time = 0.0

    for i, sentence in enumerate(sentences):
        if i == len(sentences) - 1:
            end_time = duration
        else:
            fraction = len(sentence) / total_chars
            chunk_duration = max(0.4, round(duration * fraction, 2))
            end_time = min(duration, round(current_time + chunk_duration, 2))

        if end_time < current_time:
            end_time = round(current_time + 0.1, 2)

        segments.append(
            TranscriptSegment(
                start=round(current_time, 2),
                end=round(end_time, 2),
                text=sentence,
                words=None
            )
        )
        current_time = end_time

    return segments


class ApiTranscriptionProvider(TranscriptionProvider):
    """
    Cloud / API-based Transcription Provider.
    Supports OpenAI Whisper API, Groq Whisper API, gpt-transcribe,
    and any OpenAI-compatible audio transcriptions endpoint.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint_url: str = "https://api.openai.com/v1/audio/transcriptions",
        model_name: str = "whisper-1",
        timeout: float = 180.0,
        response_format: Optional[str] = None
    ):
        self.api_key = (api_key or "").strip()
        self.endpoint_url = endpoint_url.strip() if endpoint_url else "https://api.openai.com/v1/audio/transcriptions"
        self.model_name = model_name.strip() if model_name else "whisper-1"
        self.timeout = timeout
        self.response_format = response_format.strip() if (response_format and response_format.strip()) else None

        logger.info(
            f"[ApiTranscriptionProvider] Initialized API provider: "
            f"model='{self.model_name}', endpoint='{self.endpoint_url}', "
            f"format='{self.get_active_response_format()}', key_set={bool(self.api_key)}"
        )

    @classmethod
    def get_supported_formats(cls, model_name: str) -> List[str]:
        """
        Returns list of supported response_format values for the given model.
        - gpt-transcribe and gpt-* models support ['json', 'text'].
        - whisper models (whisper-1, Groq whisper-large-v3, etc.) support
          ['verbose_json', 'json', 'text', 'srt', 'vtt'].
        """
        normalized = (model_name or "").strip().lower()
        if normalized in NON_VERBOSE_MODELS or normalized.startswith("gpt-"):
            return ["json", "text"]
        # Standard Whisper models (OpenAI, Groq, etc.)
        return ["verbose_json", "json", "text", "srt", "vtt"]

    @classmethod
    def select_response_format(cls, model_name: str, requested_format: Optional[str] = None) -> str:
        """
        Selects a compatible response_format based on the configured model.
        If an explicit requested_format is provided, validates compatibility
        and raises a clear error if incompatible.
        """
        normalized_model = (model_name or "").strip().lower()
        supported = cls.get_supported_formats(normalized_model)

        if requested_format:
            fmt = requested_format.strip().lower()
            if fmt not in supported:
                supported_desc = " or ".join(f"'{f}'" for f in supported)
                raise ValueError(
                    f"response_format '{requested_format}' is not compatible with model '{model_name}'. "
                    f"Use {supported_desc} instead."
                )
            return fmt

        # If format is not explicitly requested, automatically choose optimal format:
        # 'verbose_json' for models with rich timestamp support, otherwise 'json'
        if "verbose_json" in supported:
            return "verbose_json"
        return "json"

    def get_active_response_format(self) -> str:
        """Returns the format that will be used for the current model."""
        try:
            return self.select_response_format(self.model_name, self.response_format)
        except ValueError:
            return self.response_format or "json"

    def set_api_key(self, api_key: Optional[str]):
        """Dynamically update the API key."""
        self.api_key = (api_key or "").strip()
        logger.info(f"[ApiTranscriptionProvider] API key updated (is_set={bool(self.api_key)})")

    def set_endpoint(
        self,
        endpoint_url: str,
        model_name: Optional[str] = None,
        response_format: Optional[str] = None
    ):
        """Update endpoint, model, and optional response format."""
        if endpoint_url:
            self.endpoint_url = endpoint_url.strip()
        if model_name:
            self.model_name = model_name.strip()
        if response_format is not None:
            self.response_format = response_format.strip() if response_format.strip() else None

    def is_ready(self) -> bool:
        """API provider is ready when an API key is configured."""
        return bool(self.api_key)

    def get_info(self) -> Dict[str, Any]:
        masked_key = ""
        if self.api_key:
            if len(self.api_key) > 8:
                masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}"
            else:
                masked_key = "***"

        return {
            "provider": "api_whisper",
            "model_name": self.model_name,
            "endpoint_url": self.endpoint_url,
            "response_format": self.get_active_response_format(),
            "api_key_set": bool(self.api_key),
            "masked_key": masked_key,
            "ready": self.is_ready()
        }

    def _compress_if_needed(self, audio_path: str) -> str:
        """
        OpenAI and similar APIs have a strict 25 MB payload limit.
        If the audio file is >= 24 MB, convert to 64kbps MP3 via ffmpeg.
        """
        try:
            size_bytes = os.path.getsize(audio_path)
            if size_bytes < 24 * 1024 * 1024:
                return audio_path

            logger.info(f"[ApiTranscriptionProvider] Audio size {size_bytes / (1024*1024):.2f}MB exceeds 24MB. Compressing to MP3...")
            compressed_path = f"{audio_path}.compressed.mp3"
            cmd = [
                "ffmpeg", "-y", "-i", audio_path,
                "-vn", "-ar", "16000", "-ac", "1", "-b:a", "64k",
                compressed_path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0 and os.path.exists(compressed_path):
                new_size = os.path.getsize(compressed_path)
                logger.info(f"[ApiTranscriptionProvider] Compressed successfully to {new_size / (1024*1024):.2f}MB")
                return compressed_path
            else:
                logger.warning(f"[ApiTranscriptionProvider] ffmpeg compression failed: {result.stderr}. Using original file.")
                return audio_path
        except Exception as e:
            logger.warning(f"[ApiTranscriptionProvider] Could not compress audio: {e}. Using original file.")
            return audio_path

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        desired_language: Optional[str] = None,
        word_timestamps: bool = False,
        response_format: Optional[str] = None
    ) -> TranscriptResult:
        """
        Sends audio to cloud transcription API and extracts timestamped segments.
        Supports models that return rich segments (verbose_json) like whisper-1 and Groq,
        as well as models that only support json or text like gpt-transcribe.
        """
        if not self.is_ready():
            raise RuntimeError(
                "API Transcription provider is not configured. "
                "Please configure TRANSCRIPTION_API_KEY in backend/.env or in the VoiceScribe Settings."
            )

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        upload_path = self._compress_if_needed(audio_path)
        is_temp_compressed = (upload_path != audio_path)

        spoken_lang = language.strip().lower() if (language and language.strip().lower() != "auto") else None

        # Resolve compatible response_format
        format_override = response_format or self.response_format
        try:
            chosen_format = self.select_response_format(self.model_name, format_override)
        except ValueError as ve:
            raise RuntimeError(str(ve)) from ve

        logger.info(
            f"[ApiTranscriptionProvider] Transcribing '{upload_path}' via API "
            f"({self.endpoint_url}, model={self.model_name}, format={chosen_format}, spoken={spoken_lang or 'auto'})..."
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        data: Dict[str, Any] = {
            "model": self.model_name,
            "response_format": chosen_format
        }
        if spoken_lang:
            data["language"] = spoken_lang

        # timestamp_granularities[] is ONLY compatible with verbose_json
        if word_timestamps and chosen_format == "verbose_json":
            data["timestamp_granularities[]"] = "word"

        try:
            with open(upload_path, "rb") as f:
                filename = os.path.basename(upload_path)
                mime = "audio/mpeg" if filename.endswith(".mp3") else "audio/wav"
                files = {
                    "file": (filename, f, mime)
                }

                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        self.endpoint_url,
                        headers=headers,
                        data=data,
                        files=files
                    )

            if response.status_code == 401:
                raise RuntimeError(
                    "Cloud API Authentication Failed (HTTP 401 Unauthorized): "
                    "The provided API key is invalid or expired. Check TRANSCRIPTION_API_KEY in backend/.env."
                )
            elif response.status_code == 429:
                raise RuntimeError(
                    "Cloud API Rate Limit / Quota Exceeded (HTTP 429): "
                    "Your API account has hit a rate limit or ran out of credits."
                )
            elif response.status_code >= 400:
                err_detail = response.text
                try:
                    err_json = response.json()
                    if "error" in err_json:
                        if isinstance(err_json["error"], dict):
                            err_detail = err_json["error"].get("message", err_detail)
                        else:
                            err_detail = str(err_json["error"])
                except Exception:
                    pass

                # If the API returned a format incompatibility error
                if "response_format" in err_detail.lower() and ("not compatible" in err_detail.lower() or "compatible" in err_detail.lower()):
                    # If format wasn't explicitly forced and was verbose_json, retry with json fallback
                    if not format_override and chosen_format == "verbose_json":
                        logger.warning(
                            f"[ApiTranscriptionProvider] Model '{self.model_name}' rejected 'verbose_json': {err_detail}. "
                            f"Retrying automatically with 'json'..."
                        )
                        return self.transcribe(
                            audio_path=audio_path,
                            language=language,
                            desired_language=desired_language,
                            word_timestamps=False,
                            response_format="json"
                        )
                    raise RuntimeError(
                        f"Unsupported Model/Format Combination (HTTP {response.status_code}): {err_detail}"
                    )

                raise RuntimeError(f"Cloud API Error (HTTP {response.status_code}): {err_detail}")

            # Parse response according to chosen_format
            if chosen_format == "text":
                raw_text = response.text.strip()
                result_dict = {"text": raw_text}
            else:
                try:
                    result_dict = response.json()
                except Exception:
                    result_dict = {"text": response.text.strip()}

        except httpx.TimeoutException:
            raise RuntimeError(f"Cloud API request timed out after {self.timeout}s. The server or network was unresponsive.")
        except httpx.RequestError as e:
            raise RuntimeError(f"Cloud API network error: {str(e)}")
        finally:
            if is_temp_compressed and os.path.exists(upload_path):
                try:
                    os.remove(upload_path)
                except Exception:
                    pass

        # Parse response fields
        full_text = (
            result_dict.get("text", "").strip()
            if isinstance(result_dict, dict)
            else str(result_dict).strip()
        )
        detected_language = (
            result_dict.get("language")
            if isinstance(result_dict, dict) and result_dict.get("language")
            else (language or "unknown")
        )
        duration = float(result_dict.get("duration", 0.0)) if isinstance(result_dict, dict) else 0.0
        raw_segments = result_dict.get("segments", []) if isinstance(result_dict, dict) else []

        # If duration was not in response (common for json/text formats), calculate from audio file
        if duration <= 0.0:
            file_dur = get_audio_file_duration(audio_path)
            if file_dur > 0:
                duration = file_dur

        parsed_segments: List[TranscriptSegment] = []
        if raw_segments:
            # Preserve rich timestamped segments from verbose_json
            for seg in raw_segments:
                seg_words = None
                if word_timestamps and "words" in seg:
                    seg_words = [
                        {"word": w.get("word", ""), "start": round(float(w.get("start", 0.0)), 2), "end": round(float(w.get("end", 0.0)), 2)}
                        for w in seg.get("words", [])
                    ]

                parsed_segments.append(
                    TranscriptSegment(
                        start=round(float(seg.get("start", 0.0)), 2),
                        end=round(float(seg.get("end", 0.0)), 2),
                        text=seg.get("text", "").strip(),
                        words=seg_words
                    )
                )
            if duration <= 0.0 and parsed_segments:
                duration = parsed_segments[-1].end
        elif full_text:
            # Gracefully handle responses without timestamps (e.g. gpt-transcribe with json format)
            parsed_segments = build_fallback_segments(full_text, duration)
            if duration <= 0.0 and parsed_segments:
                duration = parsed_segments[-1].end

        logger.info(
            f"[ApiTranscriptionProvider] Transcription completed with format='{chosen_format}': "
            f"{len(parsed_segments)} segments, detected_lang='{detected_language}', duration={duration:.2f}s"
        )

        return TranscriptResult(
            text=full_text,
            segments=parsed_segments,
            language=detected_language,
            duration=round(duration, 2),
            model_name=f"Cloud API ({self.model_name})"
        )
