import React, { useState } from 'react';
import { Copy, Check, Download, FileText, Subtitles, Clock, Globe, Users, Sparkles, Cpu, Cloud } from 'lucide-react';
import { getDownloadUrl } from '../api/client';

export function TranscriptViewer({ result, onNewTranscription }) {
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState('segments'); // 'segments' | 'plain'

  if (!result) return null;

  const { id, filename, language, desired_language, duration, is_diarized, text, segments, model_name } = result;

  const isCloudApi = Boolean(
    model_name && (model_name.toLowerCase().includes('api') || model_name.toLowerCase().includes('cloud'))
  );

  const formatEngineName = (name) => {
    if (!name) return 'Whisper Turbo (Local)';
    if (name.toLowerCase().includes('api') || name.toLowerCase().includes('cloud')) {
      return name.replace(/^api-whisper\s*/i, 'Cloud API ');
    }
    if (name.includes('whisper-large-v3-turbo (turbo)')) {
      return 'Whisper Turbo (Local)';
    }
    return name.replace('whisper-large-v3-turbo', 'Whisper Turbo');
  };

  const engineDisplay = formatEngineName(model_name);

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = Math.floor(secs % 60);
    return `${mins.toString().padStart(2, '0')}:${remainingSecs.toString().padStart(2, '0')}`;
  };

  const getSpeakerColor = (speaker) => {
    if (!speaker) return 'border-slate-700 bg-slate-800/40 text-slate-300';
    if (speaker.includes('1')) return 'border-indigo-500/30 bg-indigo-500/10 text-indigo-400';
    if (speaker.includes('2')) return 'border-violet-500/30 bg-violet-500/10 text-violet-400';
    if (speaker.includes('3')) return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400';
    if (speaker.includes('4')) return 'border-amber-500/30 bg-amber-500/10 text-amber-400';
    return 'border-rose-500/30 bg-rose-500/10 text-rose-400';
  };

  const handleCopy = () => {
    let copyContent = text;
    if (viewMode === 'segments' && segments && segments.length > 0) {
      copyContent = segments
        .map(s => `[${formatTime(s.start)} - ${formatTime(s.end)}] ${s.speaker ? s.speaker + ': ' : ''}${s.text}`)
        .join('\n\n');
    }
    navigator.clipboard.writeText(copyContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = (format) => {
    if (!id) return;
    const url = getDownloadUrl(id, format);
    const a = document.createElement('a');
    a.href = url;
    a.download = '';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;

  return (
    <div className="rounded-2xl border border-slate-700/80 bg-slate-900/70 backdrop-blur-xl shadow-2xl p-6 sm:p-8 space-y-6 animate-fade-in">
      
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
            <h3 className="text-xl font-bold text-white tracking-tight">Transcription Complete</h3>
          </div>
          <p className="text-xs text-slate-400 truncate max-w-md">Source: {filename}</p>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-700 hover:border-slate-600 bg-slate-800 hover:bg-slate-750 text-slate-200 text-xs font-semibold transition-all shadow-sm"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-400" />
                <span>Copy Transcript</span>
              </>
            )}
          </button>

          {/* Download TXT */}
          <button
            onClick={() => handleDownload('txt')}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold shadow-md shadow-brand-500/20 transition-all cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download TXT</span>
          </button>

          {/* Download SRT */}
          <button
            onClick={() => handleDownload('srt')}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-violet-500/40 bg-violet-600/20 hover:bg-violet-600/30 text-violet-300 text-xs font-semibold transition-all cursor-pointer"
          >
            <Subtitles className="w-3.5 h-3.5" />
            <span>Download SRT</span>
          </button>
        </div>
      </div>

      {/* Meta Stats Badges */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3">
        <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-800 flex items-center gap-3">
          <Globe className="w-4 h-4 text-brand-400 shrink-0" />
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Language</div>
            <div className="text-sm font-semibold text-slate-200 uppercase">
              {desired_language && desired_language !== 'auto' && desired_language !== language
                ? `${language || 'Auto'} → ${desired_language}`
                : language || 'Auto'}
            </div>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-800 flex items-center gap-3">
          <Clock className="w-4 h-4 text-violet-400 shrink-0" />
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Duration</div>
            <div className="text-sm font-semibold text-slate-200">{formatTime(duration)} ({duration.toFixed(1)}s)</div>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-800 flex items-center gap-3">
          <Users className="w-4 h-4 text-pink-400 shrink-0" />
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Diarization</div>
            <div className="text-sm font-semibold text-slate-200">
              {is_diarized ? 'Multi-Speaker' : 'Single Stream'}
            </div>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-800 flex items-center gap-3">
          <FileText className="w-4 h-4 text-emerald-400 shrink-0" />
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Words</div>
            <div className="text-sm font-semibold text-slate-200">{wordCount}</div>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-800 col-span-2 sm:col-span-1 flex items-center gap-3">
          {isCloudApi ? (
            <Cloud className="w-4 h-4 text-violet-400 shrink-0" />
          ) : (
            <Cpu className="w-4 h-4 text-brand-400 shrink-0" />
          )}
          <div className="overflow-hidden">
            <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Engine</div>
            <div className="text-xs font-semibold text-slate-200 truncate" title={model_name || engineDisplay}>
              {engineDisplay}
            </div>
          </div>
        </div>
      </div>

      {/* View Switcher: Segments vs Plain Text */}
      <div className="flex items-center justify-between pt-2">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Transcript Output</div>
        <div className="flex items-center gap-1 bg-slate-800/60 p-1 rounded-xl border border-slate-700/60 text-xs">
          <button
            onClick={() => setViewMode('segments')}
            className={`px-3 py-1 rounded-lg transition-all ${
              viewMode === 'segments' ? 'bg-brand-600 text-white font-medium' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Timestamped
          </button>
          <button
            onClick={() => setViewMode('plain')}
            className={`px-3 py-1 rounded-lg transition-all ${
              viewMode === 'plain' ? 'bg-brand-600 text-white font-medium' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Full Text
          </button>
        </div>
      </div>

      {/* Transcript Text Container */}
      <div className="max-h-[460px] overflow-y-auto pr-2 space-y-3 rounded-xl">
        {viewMode === 'plain' ? (
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-slate-200 text-sm leading-relaxed whitespace-pre-wrap selection:bg-brand-500">
            {text}
          </div>
        ) : (
          segments && segments.length > 0 ? (
            segments.map((seg, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800/60 hover:border-slate-700/80 transition-all flex flex-col sm:flex-row sm:items-start gap-3 text-sm"
              >
                {/* Timestamp & Speaker Tag */}
                <div className="flex items-center sm:flex-col sm:items-start gap-2 sm:gap-1.5 shrink-0 sm:w-36">
                  <span className="font-mono text-xs text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded-md">
                    {formatTime(seg.start)} - {formatTime(seg.end)}
                  </span>
                  {seg.speaker && (
                    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-md border ${getSpeakerColor(seg.speaker)}`}>
                      {seg.speaker}
                    </span>
                  )}
                </div>

                {/* Segment Text */}
                <div className="text-slate-200 leading-relaxed flex-1">
                  {seg.text}
                </div>
              </div>
            ))
          ) : (
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-slate-200 text-sm">
              {text}
            </div>
          )
        )}
      </div>

      {/* Bottom reset button */}
      {onNewTranscription && (
        <div className="pt-4 border-t border-slate-800 flex justify-end">
          <button
            onClick={onNewTranscription}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl border border-slate-700 hover:border-slate-600 bg-slate-800 hover:bg-slate-750 text-slate-200 text-sm font-medium transition-colors"
          >
            <Sparkles className="w-4 h-4 text-brand-400" />
            <span>Transcribe Another File</span>
          </button>
        </div>
      )}

    </div>
  );
}
