# VoiceScribe: Speech-to-Text Using Deep Learning

VoiceScribe is an end-to-end web application that converts speech into timestamped text using OpenAI's **Whisper** models. It is a **dual-engine** system: run transcription **100% locally** with Whisper Large-v3 Turbo, or switch to a **Cloud Whisper API** (OpenAI / Groq) for fast results on any laptop. The engine can be changed at any time from the interface.

![Home](docs/images/home.png)

## Features

- **Audio transcription:** drag-and-drop `.wav`, `.mp3`, `.m4a`, `.aac`, `.flac`, `.ogg` files (up to 500 MB).
- **Video support:** upload `.mp4`, `.mkv`, `.mov`, `.avi`, `.webm`; audio is extracted with FFmpeg.
- **Live recording:** record from the browser microphone with a timer and waveform.
- **Two engines:** Local Whisper Large-v3 Turbo (PyTorch, CUDA float16 / CPU float32) or Cloud Whisper API (OpenAI `whisper-1`, `gpt-transcribe`, Groq Whisper).
- **Language support:** automatic language detection or manual choice from 21 languages.
- **Translation:** choose a desired output language; timestamps and speaker labels are preserved.
- **Speaker diarization:** "Speaker 1", "Speaker 2" labels using `pyannote.audio` (with a Hugging Face token) or a built-in MFCC clustering fallback.
- **Export:** timestamped view, copy to clipboard, download as `.txt` or `.srt`.
- **History:** SQLite-backed, searchable, with view, download and delete.
- **Settings dialog:** switch engines, pick OpenAI/Groq presets, store and test an API key from the UI.
- **Job queue:** one transcription runs at a time to avoid GPU/CPU memory overload; live progress stages.
- **Dark and light themes.**

| Result | History |
|---|---|
| ![Result](docs/images/result.png) | ![History](docs/images/history.png) |

## Local vs Cloud

| | Local Whisper | Cloud API |
|---|---|---|
| Where it runs | Your computer | OpenAI / Groq servers |
| Audio privacy | Audio never leaves your machine | Audio is sent over HTTPS to the provider |
| Hardware | NVIDIA GPU with ~6 GB VRAM recommended; CPU works but is slower | Any laptop |
| Cost | No API fees | Per-use billing |
| Setup | No key needed | API key required |

> **Privacy note:** in Local mode audio is never transmitted. If you choose a desired output language, the transcript **text** (not audio) is sent to a translation service (an LLM endpoint if an API key is configured, otherwise Google GTX or MyMemory). Choosing "Original / Same as Spoken" keeps everything offline.

## Prerequisites

1. **Python 3.10+** (tested on 3.12)
2. **Node.js 18+** and npm
3. **FFmpeg** on your system `PATH`
   - Windows: `winget install Gyan.FFmpeg`
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

On first run, Local mode downloads the Whisper Large-v3 Turbo weights (~1.6 GB) to `~/.cache/whisper`.

## Setup

### Backend

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

# Optional, for NVIDIA GPUs: install PyTorch with CUDA first
# pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

pip install -r requirements.txt

# Windows: copy .env.example .env     Linux/macOS: cp .env.example .env
cp .env.example .env
```

### Frontend

```bash
cd frontend
npm install
```

## Configuration (`backend/.env`)

```ini
HOST=127.0.0.1
PORT=8000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Engine: "local" (offline Whisper) or "api" (cloud Whisper)
TRANSCRIPTION_MODE=local
WHISPER_MODEL=turbo
DEVICE=auto            # auto, cuda, or cpu

# Cloud API (needed only when TRANSCRIPTION_MODE=api)
TRANSCRIPTION_API_KEY=
TRANSCRIPTION_API_URL=https://api.openai.com/v1/audio/transcriptions
TRANSCRIPTION_API_MODEL=whisper-1     # or gpt-transcribe, or whisper-large-v3-turbo for Groq
# TRANSCRIPTION_RESPONSE_FORMAT=      # optional: verbose_json, json, text

MAX_UPLOAD_SIZE_MB=500

# Optional Hugging Face token for pyannote.audio diarization.
# If empty, an MFCC clustering fallback is used.
HF_TOKEN=

DATABASE_URL=sqlite:///./storage/voicescribe.db
STORAGE_DIR=./storage
UPLOAD_DIR=./storage/uploads
```

You can also set the engine and API key from the **Settings** dialog in the app; changes are saved to `backend/.env`. **Never commit `.env`**; it is listed in `.gitignore`.

## Run

Backend (in `backend/`, venv activated):

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend (in `frontend/`):

```bash
npm run dev
```

Open http://localhost:5173.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Engine readiness, device, model, mode |
| `POST` | `/api/transcribe` | Submit a file with diarization, spoken language, desired language and provider options; returns a job ID |
| `GET` | `/api/jobs/{id}` | Job status, stage, progress (0-100), provider, model and result |
| `GET` | `/api/settings` | Current provider configuration (API key masked) |
| `POST` | `/api/settings` | Update mode, API key, endpoint, model |
| `POST` | `/api/settings/test-api` | Test the API key and endpoint |
| `GET` | `/api/history` | List transcripts (optional `search`) |
| `GET` | `/api/history/{id}` | Full transcript with segments |
| `DELETE` | `/api/history/{id}` | Delete a transcript |
| `GET` | `/api/history/{id}/download?format=txt\|srt` | Download as TXT or SRT |

## Architecture

```
React (Vite, Tailwind)  ->  FastAPI  ->  Job queue (one at a time)
                                          |-> FFmpeg + Librosa (16 kHz mono)
                                          |-> TranscriptionProvider
                                          |     |-> LocalWhisperProvider   (Whisper Large-v3 Turbo, PyTorch)
                                          |     `-> ApiTranscriptionProvider (OpenAI / Groq Whisper)
                                          |-> Diarization (pyannote / MFCC)
                                          |-> Translation (LLM -> Google GTX -> MyMemory)
                                          `-> SQLite history
```

Both engines implement the `TranscriptionProvider` interface in `backend/app/services/providers/base.py`, so the routers, job queue and frontend are the same for either engine. The Cloud provider chooses a compatible response format per model, compresses large files, and never falls back silently to Local mode.

## Tests

From `backend/`:

```bash
python test_models_transcribe.py                    # provider, format and translation unit tests
python test_integration_language_and_status.py      # job-level integration tests
python test_e2e.py                                  # needs the server running on port 8000
```

## Limitations

- Translation uses online services (LLM, Google GTX, MyMemory).
- The MFCC diarization fallback is less accurate than `pyannote.audio`.
- Job progress is kept in memory and is lost if the server restarts (saved transcripts are kept).
- The API key is stored in plain text in the local `.env`; this is intended for single-user local use.

