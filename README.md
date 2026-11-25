# VoiceScribe - Local Deep Learning Speech-to-Text System

VoiceScribe is an end-to-end, local-only web application that transcribes speech into formatted text with timestamps and speaker separation using OpenAI's **Whisper Large-v3 Turbo** neural model.

All machine learning inference runs **100% locally on your machine**. No audio or video data is ever sent to third-party or paid cloud APIs.

---

## Features

- **Audio File Transcription**: Drag-and-drop or browse `.wav`, `.mp3`, `.m4a`, `.aac`, `.flac`, `.ogg` audio files.
- **Video to Audio Extraction**: Upload `.mp4`, `.mkv`, `.mov`, `.avi`, `.webm` videos; audio is extracted via FFmpeg and transcribed automatically.
- **Speaker Diarization (Multi-Speaker)**: Separate distinct speakers in meetings and interviews ("Speaker 1", "Speaker 2", etc.) using `pyannote.audio` (if HuggingFace token provided) or built-in local MFCC + spectral clustering fallback.
- **Live In-Browser Recording**: Record speech directly from the microphone with live elapsed timer and real-time audio waveform visualization.
- **Timestamped & Subtitle Export**: View transcripts with segment timestamps and download as clean `.txt` or standard SubRip `.srt` subtitles.
- **Transcript History**: SQLite database persists all transcripts with search, full-text viewer modal, and deletion controls.
- **Local-Only Model Architecture**: Preloads Whisper Large-v3 Turbo once on server startup with automatic CUDA float16 / CPU float32 detection.
- **Concurrency Protection**: Background job queue with an execution lock prevents GPU/CPU out-of-memory errors by ensuring one active transcription at a time.

---

## Hardware Requirements & Notes

- **GPU (Recommended)**: NVIDIA GPU with CUDA support and at least **6 GB VRAM**. Whisper Large-v3 Turbo runs with `float16` precision and transcribes files several times faster than real-time.
- **CPU**: Works on any modern multi-core CPU using `float32`. CPU inference takes longer (especially on longer audio files), but produces identical high accuracy.
- **First Run Download**: On first startup, the Whisper Large-v3 Turbo weights (~1.6 GB) will be automatically downloaded and cached locally by OpenAI Whisper in `~/.cache/whisper`. Subsequent runs load immediately from disk.

---

## Prerequisites

1. **Python 3.10+** (Tested on Python 3.12)
2. **Node.js 18+ & npm**
3. **FFmpeg** installed and accessible on system `PATH`.
   - *Windows*: Download from [gyan.dev/ffmpeg](https://www.gyan.dev/ffmpeg/builds/) or install via `winget install Gyan.FFmpeg`.
   - *macOS*: `brew install ffmpeg`
   - *Linux*: `sudo apt install ffmpeg`

---

## Setup & Installation

### 1. Backend Setup

```bash
cd backend

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Optional: If you have an NVIDIA GPU, install PyTorch with CUDA first:
# pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install backend dependencies
pip install -r requirements.txt

# Configure environment variables (optional)
cp .env.example .env
```

#### Environment Variables (`backend/.env`)

```ini
HOST=127.0.0.1
PORT=8000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Provider & Model Settings
TRANSCRIPTION_MODE=local
WHISPER_MODEL=turbo
DEVICE=auto    # "auto" (detects CUDA or CPU), "cuda", or "cpu"

# Upload Limits
MAX_UPLOAD_SIZE_MB=500

# Optional HuggingFace Token for pyannote.audio diarization
# If empty, VoiceScribe falls back to local MFCC clustering automatically
HF_TOKEN=

# Storage & Database
DATABASE_URL=sqlite:///./storage/voicescribe.db
STORAGE_DIR=./storage
UPLOAD_DIR=./storage/uploads
```

### 2. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
```

---

## Running the Application

### Start Backend

In the `backend` directory (with `venv` activated):

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend server starts on `http://127.0.0.1:8000`. On first load, it will initialize the database and load Whisper Large-v3 Turbo.

### Start Frontend

In the `frontend` directory:

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173` (or `http://127.0.0.1:5173`).

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Model status, device (cuda/cpu), model name, mode |
| `POST` | `/api/transcribe` | Submit file (`audio`, `video`, `recording`) with diarization & language options |
| `GET` | `/api/jobs/{id}` | Polling status, stage, progress (0-100), and result |
| `GET` | `/api/history` | List previous transcripts with search filter |
| `GET` | `/api/history/{id}` | Full transcript detail and segment timestamps |
| `DELETE` | `/api/history/{id}` | Remove transcript from database |
| `GET` | `/api/history/{id}/download?format=txt\|srt` | Download transcript as `.txt` or `.srt` subtitle |

---

## Architecture & Future-Proofing

VoiceScribe implements a modular `TranscriptionProvider` interface (`backend/app/services/providers/base.py`):
- `LocalWhisperProvider` (`backend/app/services/providers/local_whisper.py`) runs local Whisper Large-v3 Turbo.
- A clearly documented extension point is provided for future cloud API providers (e.g. OpenAI API, custom endpoints) without changing the FastAPI routers, job queue, or frontend.
