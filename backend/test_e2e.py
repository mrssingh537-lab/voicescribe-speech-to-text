import os
import sys
import time
import requests

BASE_URL = "http://127.0.0.1:8000"

def log(msg):
    print(f"[TEST] {msg}", flush=True)

def wait_for_model_ready(timeout=300):
    log("Waiting for Whisper Large-v3 Turbo model to be loaded...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            res = requests.get(f"{BASE_URL}/api/health", timeout=5)
            if res.status_code == 200:
                data = res.json()
                if data.get("model_ready"):
                    log(f"Model is ready! (Device: {data.get('device')}, Model: {data.get('model_name')})")
                    return True
                else:
                    log("Model still downloading/loading weights into memory...")
        except Exception as e:
            log(f"Backend not responding yet: {e}")
        time.sleep(10)
    raise TimeoutError("Model did not become ready within timeout period.")

def poll_job(job_id, timeout=180):
    log(f"Polling job {job_id}...")
    start_time = time.time()
    last_stage = None
    while time.time() - start_time < timeout:
        res = requests.get(f"{BASE_URL}/api/jobs/{job_id}")
        assert res.status_code == 200, f"Failed to get job status: {res.text}"
        data = res.json()
        stage = data.get("stage")
        progress = data.get("progress")
        if stage != last_stage:
            log(f"Job {job_id} stage: {stage} ({progress}%)")
            last_stage = stage
        
        status = data.get("status")
        if status == "completed":
            log(f"Job {job_id} completed successfully!")
            return data["result"]
        elif status == "failed":
            raise RuntimeError(f"Job {job_id} failed: {data.get('error')}")
        
        time.sleep(2)
    raise TimeoutError(f"Job {job_id} timed out after {timeout} seconds.")

def run_tests():
    log("=== Starting VoiceScribe End-to-End Verification ===")

    # 1. Health check & model readiness
    wait_for_model_ready()

    # 2. Test Audio File Transcription
    audio_path = "test_speech.wav"
    assert os.path.exists(audio_path), f"Audio file {audio_path} not found"
    log(f"Submitting audio file: {audio_path}")

    with open(audio_path, "rb") as f:
        res = requests.post(
            f"{BASE_URL}/api/transcribe",
            files={"file": (os.path.basename(audio_path), f, "audio/wav")},
            data={"source_type": "audio", "diarize": "false", "language": "auto"}
        )
    assert res.status_code == 202, f"Expected 202, got {res.status_code}: {res.text}"
    audio_job_id = res.json()["job_id"]
    audio_result = poll_job(audio_job_id)
    log(f"Audio Transcript: '{audio_result['text']}'")
    assert len(audio_result["text"]) > 0, "Audio transcript should not be empty"
    assert len(audio_result["segments"]) > 0, "Segments should not be empty"
    audio_transcript_id = audio_result["id"]

    # 3. Test Video File Upload & Extraction with Diarization
    video_path = "test_video.mp4"
    assert os.path.exists(video_path), f"Video file {video_path} not found"
    log(f"Submitting video file with diarization: {video_path}")

    with open(video_path, "rb") as f:
        res = requests.post(
            f"{BASE_URL}/api/transcribe",
            files={"file": (os.path.basename(video_path), f, "video/mp4")},
            data={"source_type": "video", "diarize": "true", "language": "en"}
        )
    assert res.status_code == 202, f"Expected 202, got {res.status_code}: {res.text}"
    video_job_id = res.json()["job_id"]
    video_result = poll_job(video_job_id)
    log(f"Video Transcript: '{video_result['text']}'")
    assert len(video_result["text"]) > 0, "Video transcript should not be empty"
    assert video_result["is_diarized"] == True, "Video result should be diarized"
    # Check that segments have speakers
    for seg in video_result["segments"]:
        assert seg.get("speaker") is not None, f"Segment missing speaker label: {seg}"
        log(f"  [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['speaker']}: {seg['text']}")
    video_transcript_id = video_result["id"]

    # 4. Test History List & Search
    log("Testing History List...")
    hist_res = requests.get(f"{BASE_URL}/api/history")
    assert hist_res.status_code == 200
    history_items = hist_res.json()
    log(f"Found {len(history_items)} history items.")
    assert len(history_items) >= 2, "Expected at least 2 history records"

    log("Testing History Search...")
    search_res = requests.get(f"{BASE_URL}/api/history?search=speech")
    assert search_res.status_code == 200
    search_items = search_res.json()
    log(f"Search for 'speech' returned {len(search_items)} items.")
    assert len(search_items) >= 1

    # 5. Test History Detail
    log(f"Testing History Detail for ID {audio_transcript_id}...")
    detail_res = requests.get(f"{BASE_URL}/api/history/{audio_transcript_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == audio_transcript_id
    assert detail["filename"] == os.path.basename(audio_path)

    # 6. Test TXT and SRT Downloads
    log(f"Testing TXT Download for ID {video_transcript_id}...")
    txt_res = requests.get(f"{BASE_URL}/api/history/{video_transcript_id}/download?format=txt")
    assert txt_res.status_code == 200
    assert "VOICESCRIBE TRANSCRIPT" in txt_res.text
    log("TXT export verified successfully.")

    log(f"Testing SRT Download for ID {video_transcript_id}...")
    srt_res = requests.get(f"{BASE_URL}/api/history/{video_transcript_id}/download?format=srt")
    assert srt_res.status_code == 200
    assert "-->" in srt_res.text
    log("SRT export verified successfully.")

    # 7. Test Delete
    log(f"Testing Delete for ID {audio_transcript_id}...")
    del_res = requests.delete(f"{BASE_URL}/api/history/{audio_transcript_id}")
    assert del_res.status_code == 200
    # Verify deletion
    check_del = requests.get(f"{BASE_URL}/api/history/{audio_transcript_id}")
    assert check_del.status_code == 404, "Deleted item should return 404"
    log("Deletion verified successfully.")

    log("=== ALL END-TO-END VERIFICATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_tests()
