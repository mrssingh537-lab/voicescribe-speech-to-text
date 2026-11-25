import React from 'react';
import { Eye, Download, Trash2, FileAudio, FileVideo, Mic, Users, Clock, Globe, Cpu, Cloud } from 'lucide-react';
import { getDownloadUrl } from '../api/client';

export function HistoryItem({ item, onView, onDelete }) {
  const { id, filename, source_type, is_diarized, language, desired_language, duration, text_preview, created_at, model_name } = item;

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = Math.floor(secs % 60);
    return `${mins.toString().padStart(2, '0')}:${remainingSecs.toString().padStart(2, '0')}`;
  };

  const formatDate = (isoString) => {
    if (!isoString) return '';
    const d = new Date(isoString);
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getSourceIcon = () => {
    if (source_type === 'video') return <FileVideo className="w-4 h-4 text-violet-400" />;
    if (source_type === 'recording') return <Mic className="w-4 h-4 text-pink-400" />;
    return <FileAudio className="w-4 h-4 text-brand-400" />;
  };

  const handleDownload = (e, format) => {
    e.stopPropagation();
    const url = getDownloadUrl(id, format);
    const a = document.createElement('a');
    a.href = url;
    a.download = '';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700/80 backdrop-blur-md transition-all hover:shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
      
      {/* Left Info */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2.5 mb-1.5 flex-wrap">
          <div className="p-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60">
            {getSourceIcon()}
          </div>
          <h4 className="font-semibold text-white text-sm truncate max-w-sm sm:max-w-md">
            {filename}
          </h4>

          {/* Type Badges */}
          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
            {source_type}
          </span>
          {is_diarized && (
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md bg-violet-500/10 text-violet-300 border border-violet-500/20 flex items-center gap-1">
              <Users className="w-2.5 h-2.5" /> Multi-speaker
            </span>
          )}
          {model_name && (
            <span className={`text-[10px] font-semibold tracking-wider px-2 py-0.5 rounded-md border flex items-center gap-1 ${
              (model_name.toLowerCase().includes('api') || model_name.toLowerCase().includes('cloud'))
                ? 'bg-violet-500/10 text-violet-300 border-violet-500/20'
                : 'bg-brand-500/10 text-brand-300 border-brand-500/20'
            }`}>
              {(model_name.toLowerCase().includes('api') || model_name.toLowerCase().includes('cloud'))
                ? <Cloud className="w-2.5 h-2.5" />
                : <Cpu className="w-2.5 h-2.5" />
              }
              {model_name.toLowerCase().includes('api') || model_name.toLowerCase().includes('cloud')
                ? model_name.replace(/^api-whisper\s*/i, 'Cloud API ')
                : (model_name.includes('whisper-large-v3-turbo') ? 'Whisper Turbo' : model_name)}
            </span>
          )}
        </div>

        {/* Text Preview */}
        <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed mb-2.5">
          "{text_preview || 'No text available'}"
        </p>

        {/* Metadata Footer */}
        <div className="flex items-center gap-4 text-[11px] text-slate-500 flex-wrap">
          <span>{formatDate(created_at)}</span>
          <span>•</span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3 text-slate-400" />
            {formatTime(duration)}
          </span>
          <span>•</span>
          <span className="flex items-center gap-1 uppercase font-semibold text-slate-300">
            <Globe className="w-3 h-3 text-slate-400" />
            {desired_language && desired_language !== 'auto' && desired_language !== language
              ? `${language} → ${desired_language}`
              : language}
          </span>
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-2 self-end md:self-center shrink-0">
        <button
          onClick={() => onView(id)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-brand-600/20 hover:bg-brand-600/30 text-brand-300 border border-brand-500/30 text-xs font-semibold transition-colors"
          title="View Transcript"
        >
          <Eye className="w-3.5 h-3.5" />
          <span>View</span>
        </button>

        <button
          onClick={(e) => handleDownload(e, 'txt')}
          className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-750 text-slate-300 border border-slate-700 text-xs font-medium transition-colors"
          title="Download TXT"
        >
          <Download className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={(e) => {
            e.stopPropagation();
            if (window.confirm(`Delete transcript "${filename}"?`)) {
              onDelete(id);
            }
          }}
          className="p-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 text-xs font-medium transition-colors"
          title="Delete from history"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

    </div>
  );
}
