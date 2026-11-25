import React, { useState } from 'react';
import { 
  Cpu, 
  Cloud, 
  ShieldCheck, 
  Zap, 
  Layers, 
  FileAudio, 
  Server, 
  RefreshCw, 
  CheckCircle2, 
  Key, 
  Settings as SettingsIcon,
  Copy,
  Check,
  Terminal,
  Globe
} from 'lucide-react';

export function About() {
  const [copiedKey, setCopiedKey] = useState(false);

  const envSnippet = `# VoiceScribe Configuration (backend/.env)

# Provider Mode: "local" (default offline) or "api" (cloud-based)
TRANSCRIPTION_MODE=local

# API Provider Settings (Required when TRANSCRIPTION_MODE=api)
TRANSCRIPTION_API_KEY=your_api_key_here
TRANSCRIPTION_API_URL=https://api.openai.com/v1/audio/transcriptions
TRANSCRIPTION_API_MODEL=whisper-1

# Optional Local Device & Diarization
DEVICE=auto
WHISPER_MODEL=turbo
HF_TOKEN=`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(envSnippet);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2500);
  };

  const steps = [
    {
      num: '01',
      title: 'Audio Input & Ingestion',
      desc: 'Upload an audio file, upload a video (audio is automatically stripped via FFmpeg), or record speech live via your browser’s MediaRecorder API.',
      icon: FileAudio,
    },
    {
      num: '02',
      title: 'Signal Standardization',
      desc: 'Librosa and SoundFile standardize audio to 16,000 Hz mono PCM, normalize amplitude peaks, and trim low-frequency edge silence.',
      icon: RefreshCw,
    },
    {
      num: '03',
      title: 'Neural Inference Dispatch',
      desc: 'Audio is dispatched to your selected provider: either the offline local Whisper Large-v3 Turbo neural transformer, or the high-speed Cloud Whisper API (OpenAI / Groq).',
      icon: Cpu,
    },
    {
      num: '04',
      title: 'Diarization, Translation & Export',
      desc: 'Optional speaker turn clustering separates multiple speakers. If desired, multi-language neural translation converts the transcript into any target language, exportable as TXT and SRT subtitles.',
      icon: CheckCircle2,
    },
  ];

  const providerComparison = [
    {
      feature: 'Inference Location',
      local: '100% on your workstation (GPU/CPU)',
      api: 'Cloud servers (OpenAI / Groq)',
    },
    {
      feature: 'Privacy & Data Flow',
      local: 'Zero network calls, complete privacy',
      api: 'Sent securely over HTTPS to API endpoint',
    },
    {
      feature: 'Hardware Requirements',
      local: 'Needs ~4-6 GB RAM / GPU for fast inference',
      api: 'Runs lightweight on any laptop or VM',
    },
    {
      feature: 'Processing Speed',
      local: 'Real-time to 3x real-time depending on GPU',
      api: 'Near-instantaneous cloud GPU batching',
    },
    {
      feature: 'Configuration',
      local: 'Zero keys required; works completely offline',
      api: 'Key saved in backend/.env or via Settings UI',
    },
  ];

  const techStack = [
    { name: 'Whisper Large-v3 Turbo', role: 'State-of-the-art acoustic & language transformer model for speech transcription' },
    { name: 'Cloud Whisper API Client', role: 'Asynchronous HTTPX client supporting OpenAI Whisper and Groq Whisper endpoints' },
    { name: 'PyTorch (CUDA/CPU)', role: 'Deep learning runtime with automatic CUDA float16 and CPU float32 detection' },
    { name: 'Librosa & FFmpeg', role: 'Audio signal resampling (16kHz mono), normalization, silence trimming, and video extraction' },
    { name: 'FastAPI & SQLite', role: 'High-performance asynchronous backend with concurrency job queueing and local persistence' },
    { name: 'React, Vite & Tailwind', role: 'Modern responsive interface with dynamic provider switching and micro-animations' },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-12 animate-fade-in">
      
      {/* Intro */}
      <div className="space-y-4 text-center sm:text-left pb-6 border-b border-slate-800">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-xs font-semibold text-brand-400">
          <Layers className="w-3.5 h-3.5" />
          <span>Architecture &amp; Documentation</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">About VoiceScribe</h2>
        <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-3xl">
          VoiceScribe is an end-to-end Speech-to-Text conversion system designed for flexibility, speed, and accuracy. 
          It supports <strong>both 100% offline local inference</strong> (Whisper Large-v3 Turbo) for complete privacy, 
          and a <strong>cloud-based API provider</strong> (OpenAI / Groq) for high-speed transcription without local hardware constraints.
        </p>
      </div>

      {/* Dual Provider Comparison Cards */}
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <Server className="w-5 h-5 text-brand-400" />
          <h3 className="text-xl font-bold text-white">Dual Provider Architecture</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Local Card */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-brand-500/30 relative overflow-hidden space-y-3">
            <div className="flex items-center gap-2 text-brand-400">
              <Cpu className="w-6 h-6" />
              <h4 className="font-bold text-white text-base">Local Whisper Provider</h4>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Executes the OpenAI Whisper Large-v3 Turbo model locally using PyTorch. Ideal for sensitive meetings, confidential voice notes, medical dictation, or offline environments.
            </p>
            <div className="pt-2 flex flex-wrap gap-2 text-[11px]">
              <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">100% Offline</span>
              <span className="px-2 py-0.5 rounded-md bg-brand-500/10 text-brand-400 border border-brand-500/20 font-medium">Zero API Fees</span>
              <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 font-medium">CUDA &amp; CPU</span>
            </div>
          </div>

          {/* Cloud API Card */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-violet-500/30 relative overflow-hidden space-y-3">
            <div className="flex items-center gap-2 text-violet-400">
              <Cloud className="w-6 h-6" />
              <h4 className="font-bold text-white text-base">Cloud API Provider</h4>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Connects to OpenAI's Whisper API endpoint or Groq Cloud. Offloads neural computing to high-performance cloud clusters with rapid turnaround times and automatic file compression.
            </p>
            <div className="pt-2 flex flex-wrap gap-2 text-[11px]">
              <span className="px-2 py-0.5 rounded-md bg-violet-500/10 text-violet-400 border border-violet-500/20 font-medium">Lightning Fast</span>
              <span className="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">OpenAI &amp; Groq Compatible</span>
              <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 font-medium">Low RAM Usage</span>
            </div>
          </div>
        </div>

        {/* Comparison Table */}
        <div className="rounded-2xl bg-slate-900/60 border border-slate-800/80 overflow-hidden text-xs">
          <div className="grid grid-cols-3 bg-slate-950/80 p-3.5 font-bold text-slate-300 border-b border-slate-800">
            <div>Capability</div>
            <div className="text-brand-400 flex items-center gap-1"><Cpu className="w-3.5 h-3.5" /> Local Whisper</div>
            <div className="text-violet-400 flex items-center gap-1"><Cloud className="w-3.5 h-3.5" /> Cloud API</div>
          </div>
          <div className="divide-y divide-slate-800/60">
            {providerComparison.map((row) => (
              <div key={row.feature} className="grid grid-cols-3 p-3.5 text-slate-400 items-center">
                <span className="font-semibold text-slate-200">{row.feature}</span>
                <span className="text-slate-300">{row.local}</span>
                <span className="text-slate-300">{row.api}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Configuration & Environment Guide */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Key className="w-5 h-5 text-amber-400" />
            <h3 className="text-xl font-bold text-white">Configuration &amp; API Keys</h3>
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            All configuration is stored locally in <code className="text-brand-400 bg-slate-800 px-1.5 py-0.5 rounded font-mono text-xs">backend/.env</code>. 
            You can modify the settings file directly or use the in-app <strong>Settings Modal</strong> to test keys and switch modes on the fly.
          </p>

          <div className="relative rounded-xl bg-slate-950 border border-slate-800 p-4 font-mono text-xs text-slate-300 overflow-x-auto">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-[11px] text-slate-500">
              <span className="flex items-center gap-1.5"><Terminal className="w-3.5 h-3.5" /> backend/.env</span>
              <button
                type="button"
                onClick={copyToClipboard}
                className="flex items-center gap-1 text-slate-400 hover:text-white px-2 py-0.5 rounded bg-slate-800/60 hover:bg-slate-800 transition-colors"
              >
                {copiedKey ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copiedKey ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
            <pre className="text-slate-300 leading-relaxed">{envSnippet}</pre>
          </div>
        </div>
      </div>

      {/* 4-Step How It Works */}
      <div className="space-y-6">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <Layers className="w-5 h-5 text-brand-400" />
          <span>Processing Pipeline</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {steps.map((st) => {
            const Icon = st.icon;
            return (
              <div
                key={st.num}
                className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md relative overflow-hidden"
              >
                <span className="font-mono text-xs font-bold text-brand-400 bg-brand-500/10 px-2 py-0.5 rounded-md border border-brand-500/20 mb-3 inline-block">
                  Step {st.num}
                </span>
                <h4 className="font-semibold text-white text-base mb-1.5 flex items-center gap-2">
                  <Icon className="w-4 h-4 text-violet-400" />
                  {st.title}
                </h4>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {st.desc}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Technology Stack */}
      <div className="space-y-6">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <Server className="w-5 h-5 text-emerald-400" />
          <span>Under The Hood</span>
        </h3>

        <div className="rounded-2xl bg-slate-900/60 border border-slate-800/80 divide-y divide-slate-800/60 overflow-hidden">
          {techStack.map((tech) => (
            <div key={tech.name} className="p-4 sm:px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <span className="font-semibold text-sm text-slate-200">{tech.name}</span>
              <span className="text-xs text-slate-400">{tech.role}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Privacy Guarantee */}
      <div className="p-6 rounded-2xl bg-emerald-500/5 border border-emerald-500/20 flex items-start gap-4 text-slate-300 text-xs sm:text-sm leading-relaxed">
        <ShieldCheck className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-emerald-400 block mb-1 text-sm">Privacy &amp; Security Assurance</strong>
          When operating in <strong>Local Mode</strong>, no audio or text data ever leaves your computer. When operating in <strong>Cloud API Mode</strong>, audio is securely transmitted over TLS directly to your configured transcription provider using your personal API key stored safely in <code className="text-slate-400 bg-slate-800 px-1 py-0.5 rounded">backend/.env</code>.
        </div>
      </div>

    </div>
  );
}
