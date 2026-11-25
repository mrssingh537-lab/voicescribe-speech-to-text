import React, { useRef, useState } from 'react';
import { UploadCloud, FileAudio, FileVideo, X, CheckCircle } from 'lucide-react';

export function FileDropzone({ activeTab, selectedFile, onFileSelect, onRemoveFile, disabled }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef(null);

  const isVideo = activeTab === 'video';
  const acceptedTypes = isVideo
    ? '.mp4,.mkv,.mov,.avi,.webm'
    : '.wav,.mp3,.m4a,.aac,.flac,.ogg';

  const formatSize = (bytes) => {
    if (!bytes) return '0 B';
    const mb = bytes / (1024 * 1024);
    if (mb >= 1) return `${mb.toFixed(2)} MB`;
    return `${(bytes / 1024).toFixed(1)} KB`;
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    if (!disabled) setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  if (selectedFile) {
    return (
      <div className="relative p-6 rounded-2xl border border-brand-500/40 bg-brand-500/5 dark:bg-slate-900/60 backdrop-blur-md flex items-center justify-between transition-all">
        <div className="flex items-center gap-4 min-w-0">
          <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center shrink-0">
            {isVideo ? (
              <FileVideo className="w-6 h-6 text-brand-400" />
            ) : (
              <FileAudio className="w-6 h-6 text-brand-400" />
            )}
          </div>
          <div className="min-w-0">
            <h4 className="font-semibold text-slate-100 text-sm truncate max-w-sm sm:max-w-md">
              {selectedFile.name}
            </h4>
            <div className="flex items-center gap-2 text-xs text-slate-400 mt-0.5">
              <span>{formatSize(selectedFile.size)}</span>
              <span>•</span>
              <span className="text-brand-400 uppercase">{selectedFile.name.split('.').pop()}</span>
              <span>•</span>
              <span className="text-emerald-400 flex items-center gap-1">
                <CheckCircle className="w-3 h-3" /> Ready
              </span>
            </div>
          </div>
        </div>

        {!disabled && (
          <button
            onClick={onRemoveFile}
            className="p-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors shrink-0"
            title="Remove file"
            aria-label="Remove selected file"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`relative p-8 sm:p-12 rounded-2xl border-2 border-dashed transition-all duration-200 flex flex-col items-center justify-center text-center cursor-pointer select-none ${
        isDragOver
          ? 'border-brand-500 bg-brand-500/10 scale-[1.01]'
          : 'border-slate-700/80 hover:border-brand-500/60 bg-slate-900/30 hover:bg-slate-900/50'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={acceptedTypes}
        onChange={handleChange}
        disabled={disabled}
        className="hidden"
      />

      <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-600/20 to-violet-500/20 border border-brand-500/30 flex items-center justify-center mb-4 text-brand-400 shadow-inner">
        <UploadCloud className="w-7 h-7" />
      </div>

      <h4 className="text-base font-semibold text-slate-200 mb-1">
        Drag & drop your {isVideo ? 'video' : 'audio'} file here, or <span className="text-brand-400 underline underline-offset-2">browse</span>
      </h4>

      <p className="text-xs text-slate-400 max-w-sm mt-1">
        {isVideo
          ? 'Accepts MP4, MKV, MOV, AVI, WEBM. Audio will be extracted with FFmpeg.'
          : 'Accepts WAV, MP3, M4A, AAC, FLAC, OGG. Standardized to 16kHz mono.'}
      </p>

      <div className="mt-4 px-3 py-1 rounded-full bg-slate-800/60 border border-slate-700/50 text-[11px] text-slate-400">
        Max upload size: 500 MB
      </div>
    </div>
  );
}
