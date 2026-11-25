import os
import io
import sys
import json
import wave
import unittest
from unittest.mock import patch, MagicMock

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.providers.api_whisper import (
    ApiTranscriptionProvider,
    build_fallback_segments,
    get_audio_file_duration,
)
from app.services.providers.base import TranscriptResult, TranscriptSegment


def create_dummy_wav(path: str, duration_sec: float = 3.0):
    """Creates a small dummy wav file for testing duration and transcription."""
    sample_rate = 16000
    num_frames = int(sample_rate * duration_sec)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b'\x00\x00' * num_frames)


class TestModelFormatCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_wav = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_temp_audio.wav")
        create_dummy_wav(cls.test_wav, duration_sec=4.0)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_wav):
            try:
                os.remove(cls.test_wav)
            except OSError:
                pass

    def test_1_format_selection_not_hardcoded(self):
        """Verify format selection dynamically adapts to the configured model."""
        # 1. OpenAI Whisper-1
        fmt_whisper = ApiTranscriptionProvider.select_response_format("whisper-1")
        self.assertEqual(fmt_whisper, "verbose_json", "whisper-1 should default to verbose_json")

        # 2. GPT-Transcribe
        fmt_gpt = ApiTranscriptionProvider.select_response_format("gpt-transcribe")
        self.assertEqual(fmt_gpt, "json", "gpt-transcribe should default to json")

        # 3. Groq models
        fmt_groq_turbo = ApiTranscriptionProvider.select_response_format("whisper-large-v3-turbo")
        self.assertEqual(fmt_groq_turbo, "verbose_json", "Groq whisper-large-v3-turbo should default to verbose_json")

        fmt_groq_v3 = ApiTranscriptionProvider.select_response_format("whisper-large-v3")
        self.assertEqual(fmt_groq_v3, "verbose_json", "Groq whisper-large-v3 should default to verbose_json")

        fmt_groq_distil = ApiTranscriptionProvider.select_response_format("distil-whisper-large-v3-en")
        self.assertEqual(fmt_groq_distil, "verbose_json", "Groq distil-whisper should default to verbose_json")

        # Ensure they are not hardcoded to the same format
        self.assertNotEqual(fmt_whisper, fmt_gpt, "whisper-1 and gpt-transcribe must have different formats")
        print("[PASS] Format selection test passed: dynamic format resolution verified.")

    def test_2_unsupported_format_error(self):
        """Verify clear error is displayed when an incompatible format is requested."""
        with self.assertRaises(ValueError) as ctx:
            ApiTranscriptionProvider.select_response_format("gpt-transcribe", requested_format="verbose_json")
        
        err_msg = str(ctx.exception)
        self.assertIn("response_format 'verbose_json' is not compatible with model 'gpt-transcribe'", err_msg)
        self.assertIn("Use 'json' or 'text' instead", err_msg)
        print(f"[PASS] Unsupported format error verified: {err_msg}")

    def test_3_whisper_1_transcription(self):
        """Test transcription with whisper-1 (verbose_json with timestamps)."""
        provider = ApiTranscriptionProvider(api_key="test-key", model_name="whisper-1")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task": "transcribe",
            "language": "english",
            "duration": 4.0,
            "text": "Welcome to VoiceScribe. Have a great day.",
            "segments": [
                {"id": 0, "start": 0.0, "end": 2.1, "text": "Welcome to VoiceScribe."},
                {"id": 1, "start": 2.1, "end": 4.0, "text": "Have a great day."}
            ]
        }

        captured_post_data = {}

        def mock_post(url, headers, data, files):
            captured_post_data.update(data)
            return mock_response

        with patch("httpx.Client.post", side_effect=mock_post):
            result = provider.transcribe(self.test_wav, word_timestamps=True)

        # Check request payload
        self.assertEqual(captured_post_data["model"], "whisper-1")
        self.assertEqual(captured_post_data["response_format"], "verbose_json")
        self.assertEqual(captured_post_data.get("timestamp_granularities[]"), "word")

        # Check result
        self.assertEqual(result.text, "Welcome to VoiceScribe. Have a great day.")
        self.assertEqual(len(result.segments), 2)
        self.assertEqual(result.segments[0].start, 0.0)
        self.assertEqual(result.segments[0].end, 2.1)
        self.assertEqual(result.segments[1].end, 4.0)
        self.assertEqual(result.duration, 4.0)
        self.assertEqual(result.model_name, "Cloud API (whisper-1)")
        print("[PASS] whisper-1 transcription test passed with verbose_json and preserved timestamps.")

    def test_4_gpt_transcribe_transcription(self):
        """Test transcription with gpt-transcribe (json without timestamps, gracefully handled)."""
        provider = ApiTranscriptionProvider(api_key="test-key", model_name="gpt-transcribe")

        # gpt-transcribe only returns plain json {"text": "..."} without segments or duration
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "text": "VoiceScribe is an advanced speech-to-text platform. It supports offline and cloud AI models."
        }

        captured_post_data = {}

        def mock_post(url, headers, data, files):
            captured_post_data.update(data)
            return mock_response

        with patch("httpx.Client.post", side_effect=mock_post):
            # Even if caller passes word_timestamps=True, gpt-transcribe should NOT send timestamp_granularities
            result = provider.transcribe(self.test_wav, word_timestamps=True)

        # Check request payload
        self.assertEqual(captured_post_data["model"], "gpt-transcribe")
        self.assertEqual(captured_post_data["response_format"], "json")
        self.assertNotIn("timestamp_granularities[]", captured_post_data, "json mode must NOT send timestamp_granularities[]")

        # Check result
        self.assertEqual(result.text, "VoiceScribe is an advanced speech-to-text platform. It supports offline and cloud AI models.")
        # Segments gracefully generated from sentences
        self.assertGreaterEqual(len(result.segments), 2, "Fallback segments should split sentences")
        self.assertEqual(result.segments[0].start, 0.0)
        self.assertGreater(result.segments[0].end, 0.0)
        self.assertEqual(result.segments[-1].end, result.duration)
        self.assertGreater(result.duration, 0.0)
        self.assertEqual(result.model_name, "Cloud API (gpt-transcribe)")
        print(f"[PASS] gpt-transcribe transcription test passed with json format and {len(result.segments)} graceful segments (duration: {result.duration}s).")

    def test_5_groq_model_transcription(self):
        """Test transcription with Groq model (whisper-large-v3-turbo)."""
        provider = ApiTranscriptionProvider(
            api_key="gsk-test",
            endpoint_url="https://api.groq.com/openai/v1/audio/transcriptions",
            model_name="whisper-large-v3-turbo"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task": "transcribe",
            "language": "english",
            "duration": 4.0,
            "text": "Transcribed at lightning speed with Groq.",
            "segments": [
                {"id": 0, "start": 0.0, "end": 4.0, "text": "Transcribed at lightning speed with Groq."}
            ]
        }

        captured_post_data = {}

        def mock_post(url, headers, data, files):
            captured_post_data.update(data)
            return mock_response

        with patch("httpx.Client.post", side_effect=mock_post):
            result = provider.transcribe(self.test_wav)

        # Check request payload
        self.assertEqual(captured_post_data["model"], "whisper-large-v3-turbo")
        self.assertEqual(captured_post_data["response_format"], "verbose_json")

        # Check result
        self.assertEqual(result.text, "Transcribed at lightning speed with Groq.")
        self.assertEqual(len(result.segments), 1)
        self.assertEqual(result.duration, 4.0)
        self.assertEqual(result.model_name, "Cloud API (whisper-large-v3-turbo)")
        print("[PASS] Groq model transcription test passed with verbose_json.")

    def test_6_api_runtime_format_incompatibility_error(self):
        """Test that server-side 400 format incompatibility errors are clearly surfaced."""
        provider = ApiTranscriptionProvider(api_key="test-key", model_name="gpt-transcribe")

        # Simulate what happens if an endpoint returns the exact error from the prompt
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "response_format 'verbose_json' is not compatible with model 'gpt-transcribe'. Use 'json' or 'text' instead."
        mock_response.json.return_value = {
            "error": {
                "message": "response_format 'verbose_json' is not compatible with model 'gpt-transcribe'. Use 'json' or 'text' instead."
            }
        }

        with patch("httpx.Client.post", return_value=mock_response):
            # Explicitly force verbose_json to test error reporting
            with self.assertRaises(RuntimeError) as ctx:
                provider.transcribe(self.test_wav, response_format="verbose_json")
            
            err = str(ctx.exception)
            self.assertIn("response_format 'verbose_json' is not compatible with model 'gpt-transcribe'", err)
            print(f"[PASS] Runtime format incompatibility error surfaced clearly: {err}")

    def test_7_desired_language_translation_detection(self):
        """Verify translation requirement logic for various language pairs."""
        from app.services.translator import is_translation_needed

        self.assertTrue(is_translation_needed("en", "es"), "en -> es requires translation")
        self.assertTrue(is_translation_needed("en", "hi"), "en -> hi requires translation")
        self.assertTrue(is_translation_needed("auto", "es"), "auto -> es requires translation")
        self.assertTrue(is_translation_needed("unknown", "fr"), "unknown -> fr requires translation")
        
        # When no desired language or same as spoken, should NOT translate
        self.assertFalse(is_translation_needed("en", "auto"), "en -> auto must NOT translate")
        self.assertFalse(is_translation_needed("es", "auto"), "es -> auto must NOT translate")
        self.assertFalse(is_translation_needed("en", "en"), "en -> en must NOT translate")
        self.assertFalse(is_translation_needed("english", "en"), "english -> en must NOT translate")
        self.assertFalse(is_translation_needed("es", "es"), "es -> es must NOT translate")
        print("[PASS] Desired language requirement logic verified.")

    def test_8_translate_transcript_segments_and_alignment(self):
        """Verify translate_transcript translates segments and full_text while preserving timestamps and speakers."""
        from app.services.translator import translate_transcript, TranscriptSegment

        segments = [
            TranscriptSegment(start=0.0, end=2.5, text="Hello world", speaker="Speaker 1"),
            TranscriptSegment(start=2.5, end=5.0, text="Welcome to VoiceScribe", speaker="Speaker 2")
        ]
        full_text = "Hello world Welcome to VoiceScribe"

        with patch("app.services.translator.translate_text") as mock_trans:
            mock_trans.side_effect = lambda t, source_lang="auto", target_lang="en": (
                "Hola mundo" if "Hello" in t else "Bienvenido a VoiceScribe"
            )
            r_segs, r_text = translate_transcript(segments, full_text, "en", "es")

        self.assertEqual(len(r_segs), 2)
        self.assertEqual(r_segs[0].text, "Hola mundo")
        self.assertEqual(r_segs[0].speaker, "Speaker 1")
        self.assertEqual(r_segs[0].start, 0.0)
        self.assertEqual(r_segs[0].end, 2.5)

        self.assertEqual(r_segs[1].text, "Bienvenido a VoiceScribe")
        self.assertEqual(r_segs[1].speaker, "Speaker 2")
        self.assertEqual(r_segs[1].start, 2.5)
        self.assertEqual(r_segs[1].end, 5.0)

        self.assertEqual(r_text, "Hola mundo Bienvenido a VoiceScribe")
        print("[PASS] Transcript translation with speaker diarization and timing alignment verified.")

    def test_9_job_status_reports_model_identifier_for_cloud_api(self):
        """Verify job status includes the actual configured model identifier for Cloud API and local model name for Local."""
        from app.services.job_manager import JobManager
        from app.services.providers.api_whisper import ApiTranscriptionProvider

        manager = JobManager()
        api_prov = ApiTranscriptionProvider(api_key="sk-test", model_name="gpt-transcribe")
        manager.set_api_provider(api_prov)

        # 1. Cloud API job
        api_job_id = manager.create_job(
            filename="audio.wav",
            source_type="audio",
            diarize=False,
            language="auto",
            desired_language="auto",
            provider="api"
        )
        api_status = manager.get_job(api_job_id)
        self.assertEqual(api_status.provider, "api")
        self.assertEqual(api_status.model_name, "gpt-transcribe")

        # 2. Local Whisper job
        local_job_id = manager.create_job(
            filename="audio.wav",
            source_type="audio",
            diarize=False,
            language="auto",
            desired_language="auto",
            provider="local"
        )
        local_status = manager.get_job(local_job_id)
        self.assertEqual(local_status.provider, "local")
        self.assertEqual(local_status.model_name, "Whisper Large-v3 Turbo")
        print("[PASS] Accurate job status model identification verified for both Cloud API and Local Whisper.")

    def test_10_no_silent_fallback_from_cloud_api_to_local(self):
        """Verify that Cloud API mode does not silently fall back to Local Whisper."""
        from app.services.job_manager import JobManager

        manager = JobManager()
        # Set only local provider
        mock_local = MagicMock()
        manager.set_provider(mock_local)

        # Ensure api_provider is not set
        manager.api_provider = None

        # Mode 'api' must return None, NOT mock_local
        resolved = manager.get_provider("api")
        self.assertIsNone(resolved, "Cloud API mode must NOT silently fall back to local Whisper provider")
        print("[PASS] No silent fallback from Cloud API to Local Whisper verified.")


if __name__ == "__main__":
    unittest.main()
