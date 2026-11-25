import React from 'react';
import { Mic, Square, Play, Pause, RotateCcw, Volume2 } from 'lucide-react';

export function Recorder({ recorder, onRecordingReady, disabled }) {
  const {
    state,
    isRecording,
    isPaused,
    isStopped,
    elapsedSeconds,
    audioUrl,
    audioLevels,
    startRecording,
    pauseRecording,
    resumeRecording,
    stopRecording,
    resetRecording,
  } = recorder;

  const formatTimer = (totalSecs) => {
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleStart = async () => {
    try {
      await startRecording();
    } catch {
      // Handled in parent toast if needed
    }
  };

  return (
    <div className="p-8 sm:p-10 rounded-2xl border border-slate-700/80 bg-slate-900/40 backdrop-blur-md flex flex-col items-center justify-center text-center">
      
      {/* Live Timer */}
      <div className="font-mono text-4xl sm:text-5xl font-bold tracking-tight text-white mb-6">
        {formatTimer(elapsedSeconds)}
      </div>

      {/* Waveform Visualization Bars */}
      <div className="h-16 flex items-center justify-center gap-1.5 w-full max-w-xs mb-8">
        {audioLevels.map((lvl, idx) => (
          <div
            key={idx}
            style={{
              height: isRecording ? `${Math.max(12, lvl)}%` : isPaused ? '15%' : '8px',
              transition: isRecording ? 'height 0.1s ease' : 'height 0.3s ease',
            }}
            className={`w-2.5 rounded-full ${
              isRecording
                ? 'bg-gradient-to-t from-brand-600 via-violet-500 to-pink-500'
                : isPaused
                ? 'bg-amber-400/60'
                : 'bg-slate-700'
            }`}
          />
        ))}
      </div>

      {/* Recording Status Label */}
      <div className="mb-6 text-sm font-medium text-slate-300">
        {state === 'idle' && 'Click the microphone to start live recording'}
        {state === 'recording' && (
          <span className="flex items-center gap-2 text-rose-400">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
            Recording live from your microphone...
          </span>
        )}
        {state === 'paused' && (
          <span className="text-amber-400">Recording paused</span>
        )}
        {state === 'stopped' && (
          <span className="text-emerald-400">Recording completed. Ready for transcription.</span>
        )}
      </div>

      {/* Audio Playback Preview when stopped */}
      {audioUrl && isStopped && (
        <div className="w-full max-w-md mb-6 p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center gap-3">
          <Volume2 className="w-5 h-5 text-brand-400 shrink-0" />
          <audio src={audioUrl} controls className="w-full h-8" />
        </div>
      )}

      {/* Control Buttons */}
      <div className="flex items-center gap-4">
        {state === 'idle' && (
          <button
            onClick={handleStart}
            disabled={disabled}
            className="flex items-center gap-2.5 px-6 py-3.5 rounded-2xl bg-gradient-to-r from-rose-500 to-pink-600 hover:from-rose-600 hover:to-pink-700 text-white font-semibold shadow-lg shadow-rose-500/25 transition-all transform hover:scale-105 active:scale-95 cursor-pointer disabled:opacity-50"
          >
            <Mic className="w-5 h-5 animate-pulse" />
            <span>Start Recording</span>
          </button>
        )}

        {(isRecording || isPaused) && (
          <>
            {isRecording ? (
              <button
                onClick={pauseRecording}
                className="p-3.5 rounded-2xl bg-slate-800 border border-slate-700 hover:bg-slate-700 text-slate-200 transition-colors shadow-md"
                title="Pause"
                aria-label="Pause recording"
              >
                <Pause className="w-5 h-5" />
              </button>
            ) : (
              <button
                onClick={resumeRecording}
                className="p-3.5 rounded-2xl bg-brand-600 hover:bg-brand-500 text-white transition-colors shadow-md"
                title="Resume"
                aria-label="Resume recording"
              >
                <Play className="w-5 h-5" />
              </button>
            )}

            <button
              onClick={stopRecording}
              className="flex items-center gap-2 px-5 py-3.5 rounded-2xl bg-rose-600 hover:bg-rose-500 text-white font-semibold shadow-lg shadow-rose-600/30 transition-all cursor-pointer"
            >
              <Square className="w-5 h-5 fill-current" />
              <span>Stop</span>
            </button>
          </>
        )}

        {isStopped && (
          <button
            onClick={resetRecording}
            disabled={disabled}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-700 hover:border-slate-600 bg-slate-800/80 hover:bg-slate-750 text-slate-300 text-sm font-medium transition-colors"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Discard & Re-record</span>
          </button>
        )}
      </div>

    </div>
  );
}
