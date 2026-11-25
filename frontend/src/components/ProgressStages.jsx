import React from 'react';
import { Check, Loader2, Upload, FileAudio, Cpu, Cloud, Users, Languages, CheckCircle2 } from 'lucide-react';

export function ProgressStages({
  stage,
  progress,
  diarize,
  desiredLanguage,
  language,
  provider = 'local',
  modelName,
}) {
  const isTranslatingJob = (desiredLanguage && desiredLanguage !== 'auto' && desiredLanguage !== language) || stage === 'translating';
  const isApi = provider === 'api';
  const displayModel = modelName || (isApi ? 'whisper-1' : 'Whisper Large-v3 Turbo');
  const transcribingLabel = `Processing speech using ${displayModel}...`;

  const allStages = [
    { key: 'uploading', label: 'Uploading', icon: Upload },
    { key: 'extracting', label: 'Extracting audio', icon: FileAudio },
    { key: 'transcribing', label: 'Transcribing', icon: isApi ? Cloud : Cpu },
    ...(diarize ? [{ key: 'diarizing', label: 'Identifying speakers', icon: Users }] : []),
    ...(isTranslatingJob ? [{ key: 'translating', label: 'Translating', icon: Languages }] : []),
    { key: 'done', label: 'Done', icon: CheckCircle2 },
  ];

  const getStageIndex = (st) => {
    if (st === 'done' || st === 'saving') return allStages.length - 1;
    const found = allStages.findIndex(s => s.key === st);
    return found !== -1 ? found : 0;
  };

  const currentIndex = getStageIndex(stage);

  return (
    <div className="p-6 rounded-2xl bg-slate-900/80 border border-brand-500/30 backdrop-blur-md shadow-2xl">
      {/* Stage Steps */}
      <div className="flex items-center justify-between relative mb-6">
        {allStages.map((s, idx) => {
          const Icon = s.icon;
          const isDone = idx < currentIndex || stage === 'done';
          const isCurrent = idx === currentIndex && stage !== 'done';
          const isPending = idx > currentIndex;

          return (
            <div key={s.key} className="flex flex-col items-center flex-1 relative z-10">
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 ${
                  isDone
                    ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30'
                    : isCurrent
                    ? 'bg-brand-600 text-white shadow-lg shadow-brand-500/40 ring-4 ring-brand-500/20 animate-pulse'
                    : 'bg-slate-800 text-slate-500 border border-slate-700'
                }`}
              >
                {isDone ? (
                  <Check className="w-5 h-5 stroke-[2.5]" />
                ) : isCurrent ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </div>
              <span
                className={`text-xs mt-2 font-medium text-center transition-colors px-1 ${
                  isDone
                    ? 'text-emerald-400'
                    : isCurrent
                    ? 'text-brand-300 font-semibold'
                    : 'text-slate-500'
                }`}
              >
                {s.label}
              </span>
            </div>
          );
        })}

        {/* Connecting Line */}
        <div className="absolute top-5 left-8 right-8 h-0.5 bg-slate-800 -z-0">
          <div
            className="h-full bg-gradient-to-r from-brand-500 to-emerald-500 transition-all duration-500"
            style={{
              width: `${(Math.min(currentIndex, allStages.length - 1) / (allStages.length - 1)) * 100}%`
            }}
          />
        </div>
      </div>

      {/* Progress Bar & Percentage */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-slate-400 font-medium">
          <span className="flex items-center gap-2">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-400" />
            <span>
              {stage === 'translating'
                ? 'Translating transcript into desired output language...'
                : stage === 'diarizing'
                ? 'Distinguishing and clustering unique speakers...'
                : stage === 'extracting'
                ? 'Extracting and normalizing audio tracks...'
                : transcribingLabel}
            </span>
          </span>
          <span className="font-mono text-brand-400 font-semibold">{progress}%</span>
        </div>
        <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-brand-600 via-violet-500 to-pink-500 transition-all duration-300 rounded-full"
            style={{ width: `${Math.max(5, progress)}%` }}
          />
        </div>
      </div>
    </div>
  );
}
