import os
import logging
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import librosa
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score
from app.config import settings
from app.services.providers.base import TranscriptSegment

logger = logging.getLogger("voicescribe.diarization")


class DiarizationService:
    """
    Speaker diarization service supporting:
    1. pyannote.audio pretrained pipeline (if HF_TOKEN is configured in .env)
    2. Lightweight, zero-config local MFCC + spectral clustering fallback
    """

    def __init__(self, hf_token: Optional[str] = None):
        self.hf_token = hf_token or settings.HF_TOKEN
        self.pyannote_pipeline = None
        self._init_attempted = False

    def _init_pyannote(self):
        if self._init_attempted:
            return
        self._init_attempted = True

        if not self.hf_token:
            logger.info("[Diarization] No HF_TOKEN provided; using local MFCC clustering fallback.")
            return

        try:
            from pyannote.audio import Pipeline
            logger.info("[Diarization] Loading pyannote.audio speaker-diarization pipeline...")
            self.pyannote_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.hf_token
            )
            # Send to CUDA if available
            import torch
            if torch.cuda.is_available():
                self.pyannote_pipeline.to(torch.device("cuda"))
            logger.info("[Diarization] pyannote.audio pipeline initialized successfully.")
        except Exception as e:
            logger.warning(
                f"[Diarization] Failed to initialize pyannote.audio ({e}). "
                f"Falling back to local MFCC clustering."
            )
            self.pyannote_pipeline = None

    def diarize_segments(
        self,
        audio_path: str,
        segments: List[TranscriptSegment]
    ) -> List[TranscriptSegment]:
        """
        Assigns speaker labels (e.g. 'Speaker 1', 'Speaker 2') to each segment.
        """
        if not segments:
            return segments

        # If only 1 segment, simply label Speaker 1
        if len(segments) == 1:
            segments[0].speaker = "Speaker 1"
            return segments

        self._init_pyannote()

        if self.pyannote_pipeline is not None:
            try:
                return self._diarize_pyannote(audio_path, segments)
            except Exception as e:
                logger.error(f"[Diarization] pyannote inference failed ({e}), using MFCC fallback.", exc_info=True)

        return self._diarize_mfcc_clustering(audio_path, segments)

    def _diarize_pyannote(
        self,
        audio_path: str,
        segments: List[TranscriptSegment]
    ) -> List[TranscriptSegment]:
        logger.info(f"[Diarization] Running pyannote pipeline on '{audio_path}'")
        diarization_output = self.pyannote_pipeline(audio_path)

        # Build list of (start, end, raw_speaker)
        speaker_turns: List[Tuple[float, float, str]] = []
        for turn, _, speaker in diarization_output.itertracks(yield_label=True):
            speaker_turns.append((turn.start, turn.end, speaker))

        if not speaker_turns:
            logger.warning("[Diarization] No speakers identified by pyannote; defaulting to Speaker 1.")
            for seg in segments:
                seg.speaker = "Speaker 1"
            return segments

        # Create mapping from raw speaker names (e.g. SPEAKER_00) to Speaker 1, 2, ...
        raw_speakers_seen = {}
        speaker_counter = 1

        for seg in segments:
            # Find the speaker with the maximum overlap with this segment
            seg_start = seg.start
            seg_end = seg.end
            overlaps: Dict[str, float] = {}

            for turn_start, turn_end, spk in speaker_turns:
                overlap_start = max(seg_start, turn_start)
                overlap_end = min(seg_end, turn_end)
                if overlap_end > overlap_start:
                    dur = overlap_end - overlap_start
                    overlaps[spk] = overlaps.get(spk, 0.0) + dur

            if overlaps:
                dominant_spk = max(overlaps, key=overlaps.get)
            else:
                # Find nearest speaker turn
                dominant_spk = min(speaker_turns, key=lambda t: abs(t[0] - seg_start))[2]

            if dominant_spk not in raw_speakers_seen:
                raw_speakers_seen[dominant_spk] = f"Speaker {speaker_counter}"
                speaker_counter += 1

            seg.speaker = raw_speakers_seen[dominant_spk]

        return segments

    def _diarize_mfcc_clustering(
        self,
        audio_path: str,
        segments: List[TranscriptSegment]
    ) -> List[TranscriptSegment]:
        """
        Lightweight zero-dependency local diarization using Librosa MFCC extraction
        and unsupervised clustering to separate distinct speakers.
        """
        logger.info(f"[Diarization] Running local MFCC feature clustering on {len(segments)} segments")
        try:
            y, sr = librosa.load(audio_path, sr=16000, mono=True)
        except Exception as e:
            logger.error(f"[Diarization] Could not load audio for MFCC extraction: {e}")
            for seg in segments:
                seg.speaker = "Speaker 1"
            return segments

        features = []
        valid_indices = []

        for idx, seg in enumerate(segments):
            start_sample = int(seg.start * sr)
            end_sample = int(seg.end * sr)
            seg_audio = y[start_sample:end_sample]

            # Require at least 0.15s of audio for meaningful MFCC computation
            if len(seg_audio) < int(sr * 0.15):
                continue

            try:
                # Extract 20 MFCCs + deltas
                mfcc = librosa.feature.mfcc(y=seg_audio, sr=sr, n_mfcc=20)
                mfcc_mean = np.mean(mfcc, axis=1)
                mfcc_std = np.std(mfcc, axis=1)
                delta_mfcc = librosa.feature.delta(mfcc)
                delta_mean = np.mean(delta_mfcc, axis=1)

                feature_vec = np.hstack([mfcc_mean, mfcc_std, delta_mean])
                features.append(feature_vec)
                valid_indices.append(idx)
            except Exception as feat_err:
                logger.debug(f"Failed extracting features for segment {idx}: {feat_err}")

        # If too few valid segments for multi-speaker clustering
        if len(features) < 2:
            for seg in segments:
                seg.speaker = "Speaker 1"
            return segments

        X = np.array(features)
        num_segments = len(X)

        # Determine number of clusters k
        max_k = min(5, num_segments - 1)
        best_k = 2
        best_score = -1.0

        if max_k >= 2 and num_segments > 3:
            for k in range(2, max_k + 1):
                try:
                    clusterer = AgglomerativeClustering(n_clusters=k)
                    labels = clusterer.fit_predict(X)
                    score = silhouette_score(X, labels)
                    if score > best_score:
                        best_score = score
                        best_k = k
                except Exception:
                    pass
        else:
            best_k = min(2, num_segments)

        logger.info(f"[Diarization] Local clustering identified optimal speakers k={best_k}")
        final_clusterer = AgglomerativeClustering(n_clusters=best_k)
        labels = final_clusterer.fit_predict(X)

        # Order clusters by their first appearance in the timeline
        label_order = {}
        counter = 1
        for lbl in labels:
            if lbl not in label_order:
                label_order[lbl] = f"Speaker {counter}"
                counter += 1

        # Assign speaker labels to valid segments
        for valid_idx, lbl in zip(valid_indices, labels):
            segments[valid_idx].speaker = label_order[lbl]

        # Fill in any short/skipped segments from their closest neighbor
        last_known = "Speaker 1"
        for seg in segments:
            if seg.speaker is None:
                seg.speaker = last_known
            else:
                last_known = seg.speaker

        return segments


diarization_service = DiarizationService()
