import json
from typing import List, Dict, Any


def format_seconds_to_srt_time(seconds: float) -> str:
    """Format seconds float into SubRip time code: HH:MM:SS,mmm"""
    total_ms = int(round(seconds * 1000))
    hours = total_ms // 3600000
    total_ms %= 3600000
    minutes = total_ms // 60000
    total_ms %= 60000
    secs = total_ms // 1000
    millis = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_seconds_to_human_time(seconds: float) -> str:
    """Format seconds float into human readable time: MM:SS or HH:MM:SS"""
    total_secs = int(round(seconds))
    hours = total_secs // 3600
    minutes = (total_secs % 3600) // 60
    secs = total_secs % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def export_txt(transcript: Any) -> str:
    """
    Exports transcript to formatted plain text document.
    """
    filename = getattr(transcript, "filename", "transcript")
    language = getattr(transcript, "language", "auto")
    duration = getattr(transcript, "duration", 0.0)
    created_at = getattr(transcript, "created_at", "")
    full_text = getattr(transcript, "text", "")
    is_diarized = getattr(transcript, "is_diarized", False)

    segments_raw = getattr(transcript, "segments_json", "[]")
    if isinstance(segments_raw, str):
        try:
            segments = json.loads(segments_raw)
        except Exception:
            segments = []
    elif isinstance(segments_raw, list):
        segments = segments_raw
    else:
        segments = []

    lines = []
    lines.append("=" * 60)
    lines.append(f"VOICESCRIBE TRANSCRIPT: {filename}")
    lines.append("=" * 60)
    lines.append(f"Date:     {created_at}")
    lines.append(f"Duration: {format_seconds_to_human_time(duration)} ({duration:.2f}s)")
    desired_language = getattr(transcript, "desired_language", "auto")
    if desired_language and desired_language != "auto" and desired_language.lower() != language.lower():
        lines.append(f"Language: {language.upper()} -> {desired_language.upper()} (Translated)")
    else:
        lines.append(f"Language: {language.upper()}")
    lines.append(f"Diarized: {'Yes (Speaker-labeled)' if is_diarized else 'No'}")
    lines.append("-" * 60)
    lines.append("")

    if segments:
        for seg in segments:
            start_str = format_seconds_to_human_time(seg.get("start", 0.0))
            end_str = format_seconds_to_human_time(seg.get("end", 0.0))
            speaker = seg.get("speaker")
            text = seg.get("text", "").strip()

            if speaker:
                lines.append(f"[{start_str} - {end_str}] {speaker}:")
            else:
                lines.append(f"[{start_str} - {end_str}]:")
            lines.append(f"  {text}")
            lines.append("")
    else:
        lines.append(full_text)

    lines.append("=" * 60)
    return "\n".join(lines)


def export_srt(transcript: Any) -> str:
    """
    Exports transcript to standard SubRip (.srt) subtitle format.
    """
    segments_raw = getattr(transcript, "segments_json", "[]")
    if isinstance(segments_raw, str):
        try:
            segments = json.loads(segments_raw)
        except Exception:
            segments = []
    elif isinstance(segments_raw, list):
        segments = segments_raw
    else:
        segments = []

    if not segments:
        # Fallback if no segments stored
        duration = getattr(transcript, "duration", 5.0)
        full_text = getattr(transcript, "text", "")
        return (
            f"1\n"
            f"00:00:00,000 --> {format_seconds_to_srt_time(duration)}\n"
            f"{full_text}\n\n"
        )

    srt_entries = []
    for idx, seg in enumerate(segments, 1):
        start_time = format_seconds_to_srt_time(seg.get("start", 0.0))
        end_time = format_seconds_to_srt_time(seg.get("end", 0.0))
        speaker = seg.get("speaker")
        text = seg.get("text", "").strip()

        subtitle_text = f"[{speaker}] {text}" if speaker else text

        srt_entries.append(
            f"{idx}\n"
            f"{start_time} --> {end_time}\n"
            f"{subtitle_text}\n"
        )

    return "\n".join(srt_entries)
