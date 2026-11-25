import os
import sys
import asyncio
import shutil
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.database import init_db
from app.services.job_manager import JobManager
from app.services.providers.api_whisper import ApiTranscriptionProvider


class TestLanguageAndStatusIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.backend_dir = os.path.dirname(os.path.abspath(__file__))
        cls.src_wav = os.path.join(cls.backend_dir, "test_speech.wav")
        assert os.path.exists(cls.src_wav), "test_speech.wav must exist"

    def test_cloud_api_desired_language_and_model_status(self):
        """Test full transcription with Cloud API + desired output language (Spanish)."""
        api_key = os.getenv("TRANSCRIPTION_API_KEY")
        if not api_key:
            self.skipTest("No TRANSCRIPTION_API_KEY configured")

        manager = JobManager()
        api_prov = ApiTranscriptionProvider(api_key=api_key, model_name="gpt-transcribe")
        manager.set_api_provider(api_prov)

        temp_wav = os.path.join(self.backend_dir, "temp_integration_speech.wav")
        shutil.copy(self.src_wav, temp_wav)

        job_id = manager.create_job(
            filename="test_speech.wav",
            source_type="audio",
            diarize=False,
            language="en",
            desired_language="es",
            provider="api"
        )

        # Check immediate status before completion
        status_before = manager.get_job(job_id)
        self.assertEqual(status_before.provider, "api")
        self.assertEqual(status_before.model_name, "gpt-transcribe")

        # Run job
        asyncio.run(
            manager.process_job(
                job_id=job_id,
                temp_input_path=temp_wav,
                filename="test_speech.wav",
                source_type="audio",
                diarize=False,
                language="en",
                desired_language="es",
                provider="api"
            )
        )

        job_after = manager.get_job(job_id)
        self.assertEqual(job_after.status, "completed")
        self.assertEqual(job_after.provider, "api")
        self.assertEqual(job_after.model_name, "gpt-transcribe")
        self.assertIsNotNone(job_after.result)
        self.assertEqual(job_after.result.language, "en")
        self.assertEqual(job_after.result.desired_language, "es")

        result_text = job_after.result.text.lower()
        print(f"\n[INTEGRATION TEST] Translated result: '{job_after.result.text}'")
        # Ensure Spanish text was produced (e.g. contains 'bienvenido' or 'es' or 'de')
        self.assertTrue(
            "bienvenido" in result_text or "reconocimiento" in result_text or "sistema" in result_text or "voz" in result_text,
            f"Expected Spanish translated text, got: {job_after.result.text}"
        )
        print("[PASS] Integration test passed: Spanish desired language output and model identifier verified.")

    def test_local_mode_desired_language_and_model_status(self):
        """Test Local Whisper mode status and desired output language translation."""
        from app.services.providers.base import TranscriptionProvider, TranscriptResult, TranscriptSegment

        class MockLocalProvider(TranscriptionProvider):
            def __init__(self):
                self.model_name = "turbo"
            def is_ready(self):
                return True
            def get_info(self):
                return {"provider": "local", "model_name": "turbo"}
            def transcribe(self, audio_path, language=None, desired_language=None, word_timestamps=False):
                return TranscriptResult(
                    text="Hello and welcome to VoiceScribe. Have a wonderful day.",
                    segments=[
                        TranscriptSegment(start=0.0, end=2.0, text="Hello and welcome to VoiceScribe.", speaker=None),
                        TranscriptSegment(start=2.0, end=4.0, text="Have a wonderful day.", speaker=None)
                    ],
                    language="en",
                    duration=4.0,
                    model_name="Whisper Turbo (Local)"
                )

        manager = JobManager()
        local_prov = MockLocalProvider()
        manager.set_provider(local_prov)

        temp_wav = os.path.join(self.backend_dir, "temp_local_speech.wav")
        shutil.copy(self.src_wav, temp_wav)

        job_id = manager.create_job(
            filename="test_speech.wav",
            source_type="audio",
            diarize=False,
            language="en",
            desired_language="fr",
            provider="local"
        )

        status_before = manager.get_job(job_id)
        self.assertEqual(status_before.provider, "local")
        self.assertEqual(status_before.model_name, "Whisper Large-v3 Turbo")

        asyncio.run(
            manager.process_job(
                job_id=job_id,
                temp_input_path=temp_wav,
                filename="test_speech.wav",
                source_type="audio",
                diarize=False,
                language="en",
                desired_language="fr",
                provider="local"
            )
        )

        job_after = manager.get_job(job_id)
        self.assertEqual(job_after.status, "completed")
        self.assertEqual(job_after.provider, "local")
        self.assertEqual(job_after.model_name, "Whisper Large-v3 Turbo")
        self.assertIsNotNone(job_after.result)
        self.assertEqual(job_after.result.desired_language, "fr")

        result_text = job_after.result.text.lower()
        print(f"\n[INTEGRATION TEST LOCAL] French translated result: '{job_after.result.text}'")
        self.assertTrue(
            "bonjour" in result_text or "bienvenue" in result_text or "journée" in result_text or "bonne" in result_text,
            f"Expected French translated text, got: {job_after.result.text}"
        )
        print("[PASS] Local Whisper integration test passed: French desired language output and local model name verified.")


if __name__ == "__main__":
    unittest.main()
