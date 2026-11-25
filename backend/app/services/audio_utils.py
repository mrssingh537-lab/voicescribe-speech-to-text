import os
import subprocess
import logging
from typing import Tuple, Dict, Any
import numpy as np
import soundfile as sf
import librosa

logger = logging.getLogger("voicescribe.audio_utils")

AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".wma"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv"}


def is_video_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in VIDEO_EXTENSIONS


def is_audio_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in AUDIO_EXTENSIONS or ext in {".webm", ".ogg"}


def extract_audio_from_video(video_path: str, output_wav_path: str) -> str:
    """
    Extracts audio from a video container using ffmpeg and converts directly
    to 16kHz mono 16-bit PCM WAV.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vn",                 # Disable video recording
        "-acodec", "pcm_s16le", # 16-bit PCM WAV
        "-ar", "16000",        # 16kHz sample rate
        "-ac", "1",            # Mono
        output_wav_path
    ]

    logger.info(f"Extracting audio from video: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        logger.error(f"FFmpeg error: {result.stderr}")
        raise RuntimeError(f"FFmpeg failed to extract audio from video: {result.stderr}")

    if not os.path.exists(output_wav_path) or os.path.getsize(output_wav_path) == 0:
        raise RuntimeError("FFmpeg completed but output audio file is missing or empty.")

    return output_wav_path


def standardize_audio(input_path: str, output_wav_path: str) -> Dict[str, Any]:
    """
    Standardizes any audio/video input to 16kHz mono, normalized, silence-trimmed WAV.
    Computes duration and audio statistics.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    temp_intermediate = None
    source_to_load = input_path

    # If input is video, first extract audio with ffmpeg
    if is_video_file(input_path):
        temp_intermediate = output_wav_path + ".extracted.wav"
        extract_audio_from_video(input_path, temp_intermediate)
        source_to_load = temp_intermediate

    try:
        # Load audio and resample to 16kHz mono via Librosa
        logger.info(f"Loading and resampling '{source_to_load}' to 16kHz mono...")
        try:
            y, sr = librosa.load(source_to_load, sr=16000, mono=True)
        except Exception as load_err:
            logger.warning(f"Librosa direct load failed ({load_err}), attempting ffmpeg transcode fallback...")
            # Fallback for weird formats (e.g. browser WebM/Opus)
            fallback_wav = output_wav_path + ".fallback.wav"
            cmd = ["ffmpeg", "-y", "-i", source_to_load, "-ar", "16000", "-ac", "1", fallback_wav]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            y, sr = librosa.load(fallback_wav, sr=16000, mono=True)
            if os.path.exists(fallback_wav):
                try:
                    os.remove(fallback_wav)
                except OSError:
                    pass

        # Trim low-amplitude silence at edges (top_db=35)
        # Keep non-silent interval to prevent empty audio on quiet clips
        y_trimmed, _ = librosa.effects.trim(y, top_db=35)
        if len(y_trimmed) > sr * 0.2:  # at least 200ms
            y = y_trimmed

        # Normalize audio peak to -1.0 to 1.0
        max_amp = np.max(np.abs(y))
        if max_amp > 1e-5:
            y = y / max_amp * 0.95

        # Compute duration
        duration = float(librosa.get_duration(y=y, sr=sr))

        # Write out standardized 16-bit PCM WAV
        sf.write(output_wav_path, y, sr, subtype="PCM_16")
        logger.info(f"Standardized audio saved to '{output_wav_path}' (duration: {duration:.2f}s)")

        return {
            "wav_path": output_wav_path,
            "duration": round(duration, 2),
            "sample_rate": sr,
            "channels": 1
        }
    finally:
        if temp_intermediate and os.path.exists(temp_intermediate):
            try:
                os.remove(temp_intermediate)
            except OSError:
                pass
