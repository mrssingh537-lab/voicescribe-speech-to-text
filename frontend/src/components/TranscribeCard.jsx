import React from 'react';
import { TabSwitcher } from './TabSwitcher';
import { FileDropzone } from './FileDropzone';
import { Recorder } from './Recorder';
import { ProgressStages } from './ProgressStages';
import { 
  Users, 
  Globe, 
  Languages, 
  Sparkles, 
  AlertCircle, 
  Info, 
  Cpu, 
  Cloud, 
  Key, 
  CheckCircle2, 
  ShieldCheck, 
  Settings as SettingsIcon 
} from 'lucide-react';

const SPOKEN_LANGUAGES = [
  { code: 'auto', name: 'Auto Detect Language' },
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'Hindi (हिंदी)' },
  { code: 'es', name: 'Spanish (Español)' },
  { code: 'fr', name: 'French (Français)' },
  { code: 'de', name: 'German (Deutsch)' },
  { code: 'ja', name: 'Japanese (日本語)' },
  { code: 'zh', name: 'Chinese (中文)' },
  { code: 'pt', name: 'Portuguese (Português)' },
  { code: 'ar', name: 'Arabic (العربية)' },
  { code: 'ru', name: 'Russian (Русский)' },
  { code: 'it', name: 'Italian (Italiano)' },
  { code: 'ko', name: 'Korean (한국어)' },
  { code: 'tr', name: 'Turkish (Türkçe)' },
  { code: 'nl', name: 'Dutch (Nederlands)' },
  { code: 'bn', name: 'Bengali (বাংলা)' },
  { code: 'ta', name: 'Tamil (தமிழ்)' },
  { code: 'te', name: 'Telugu (తెలుగు)' },
  { code: 'mr', name: 'Marathi (मराठी)' },
  { code: 'ur', name: 'Urdu (اردو)' },
  { code: 'gu', name: 'Gujarati (ગુજરાતી)' },
  { code: 'pa', name: 'Punjabi (ਪੰਜਾਬੀ)' },
];

const DESIRED_LANGUAGES = [
  { code: 'auto', name: 'Original / Same as Spoken' },
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'Hindi (हिंदी)' },
  { code: 'es', name: 'Spanish (Español)' },
  { code: 'fr', name: 'French (Français)' },
  { code: 'de', name: 'German (Deutsch)' },
  { code: 'ja', name: 'Japanese (日本語)' },
  { code: 'zh', name: 'Chinese (中文)' },
  { code: 'pt', name: 'Portuguese (Português)' },
  { code: 'ar', name: 'Arabic (العربية)' },
  { code: 'ru', name: 'Russian (Русский)' },
  { code: 'it', name: 'Italian (Italiano)' },
  { code: 'ko', name: 'Korean (한국어)' },
  { code: 'tr', name: 'Turkish (Türkçe)' },
  { code: 'nl', name: 'Dutch (Nederlands)' },
  { code: 'bn', name: 'Bengali (বাংলা)' },
  { code: 'ta', name: 'Tamil (தமிழ்)' },
  { code: 'te', name: 'Telugu (తెలుగు)' },
  { code: 'mr', name: 'Marathi (मराठी)' },
  { code: 'ur', name: 'Urdu (اردو)' },
  { code: 'gu', name: 'Gujarati (ગુજરાતી)' },
  { code: 'pa', name: 'Punjabi (ਪੰਜਾਬੀ)' },
];

export function TranscribeCard({
  activeTab,
  setActiveTab,
  selectedFile,
  setSelectedFile,
  recorder,
  diarize,
  setDiarize,
  language,
  setLanguage,
  desiredLanguage,
  setDesiredLanguage,
  provider,
  setProvider,
  settingsInfo,
  onOpenSettings,
  onSubmit,
  isProcessing,
  currentStage,
  progress,
  jobData,
  modelReady,
  errorMessage,
}) {
  const isRecordingTab = activeTab === 'record';
  const hasInput = isRecordingTab ? !!recorder.audioBlob : !!selectedFile;
  const isApiKeyMissing = provider === 'api' && !settingsInfo?.api_key_configured;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!hasInput || isProcessing) return;
    if (isApiKeyMissing) {
      onOpenSettings?.();
      return;
    }

    if (isRecordingTab) {
      // Package recorded audio blob into a File object
      const recordedFile = new File([recorder.audioBlob], `recording_${Date.now()}.webm`, {
        type: recorder.audioBlob.type || 'audio/webm'
      });
      onSubmit(recordedFile, 'recording', provider);
    } else {
      onSubmit(selectedFile, activeTab, provider);
    }
  };

  return (
    <div className="rounded-3xl border border-slate-800/80 bg-slate-900/60 backdrop-blur-xl shadow-2xl p-6 sm:p-8 space-y-6">
      
      {/* Provider Selector Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 sm:px-4 rounded-2xl bg-slate-950/60 border border-slate-800/80">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-400">Mode:</span>
          <div className="inline-flex p-1 rounded-xl bg-slate-900 border border-slate-800">
            <button
              type="button"
              onClick={() => setProvider('local')}
              disabled={isProcessing}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                provider === 'local'
                  ? 'bg-brand-600 text-white shadow-md shadow-brand-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>Local Offline</span>
            </button>
            <button
              type="button"
              onClick={() => setProvider('api')}
              disabled={isProcessing}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                provider === 'api'
                  ? 'bg-violet-600 text-white shadow-md shadow-violet-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Cloud className="w-3.5 h-3.5" />
              <span>Cloud API</span>
            </button>
          </div>
        </div>

        {/* Status / Configure button */}
        <div className="flex items-center justify-between sm:justify-end gap-2 text-xs">
          {provider === 'api' ? (
            settingsInfo?.api_key_configured ? (
              <span className="text-emerald-400 flex items-center gap-1 font-medium bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>API Ready ({settingsInfo?.api_model || 'whisper-1'})</span>
              </span>
            ) : (
              <button
                type="button"
                onClick={onOpenSettings}
                className="px-2.5 py-1 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-bold hover:bg-amber-500/30 flex items-center gap-1 transition-colors animate-pulse"
              >
                <Key className="w-3 h-3" />
                <span>API Key Required</span>
              </button>
            )
          ) : (
            <span className="text-slate-400 flex items-center gap-1 font-medium bg-slate-800/40 px-2.5 py-1 rounded-lg border border-slate-700/50">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>100% Offline (Large-v3 Turbo)</span>
            </span>
          )}

          <button
            type="button"
            onClick={onOpenSettings}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 border border-transparent hover:border-slate-700 transition-colors"
            title="Configure Provider Settings"
          >
            <SettingsIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 3 Tabs */}
      <TabSwitcher
        activeTab={activeTab}
        onChangeTab={(tab) => {
          setActiveTab(tab);
          if (tab !== 'record') {
            recorder.resetRecording();
          }
        }}
        disabled={isProcessing}
      />

      {/* Input Section */}
      <div className="pt-2">
        {isRecordingTab ? (
          <Recorder
            recorder={recorder}
            disabled={isProcessing}
          />
        ) : (
          <FileDropzone
            activeTab={activeTab}
            selectedFile={selectedFile}
            onFileSelect={(file) => setSelectedFile(file)}
            onRemoveFile={() => setSelectedFile(null)}
            disabled={isProcessing}
          />
        )}
      </div>

      {/* Options Bar: Spoken Language, Desired Language, and Diarization Toggle */}
      <div className="space-y-4 p-4 sm:p-5 rounded-2xl bg-slate-950/40 border border-slate-800/80">
        
        {/* Language Selectors Row: Spoken Language beside Desired Language */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          
          {/* Spoken Language */}
          <div className="space-y-1.5">
            <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
              <Globe className="w-3.5 h-3.5 text-brand-400" />
              <span>Spoken Language (Input)</span>
            </label>
            <div className="relative">
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                disabled={isProcessing}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/50 transition-all cursor-pointer disabled:opacity-50"
              >
                {SPOKEN_LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>
            <p className="text-[11px] text-slate-500">
              Language spoken in audio or auto-detected.
            </p>
          </div>

          {/* Desired Language (Output Target) */}
          <div className="space-y-1.5">
            <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
              <Languages className="w-3.5 h-3.5 text-violet-400" />
              <span>Desired Language (Output)</span>
            </label>
            <div className="relative">
              <select
                value={desiredLanguage}
                onChange={(e) => setDesiredLanguage(e.target.value)}
                disabled={isProcessing}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all cursor-pointer disabled:opacity-50"
              >
                {DESIRED_LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>
            <p className="text-[11px] text-slate-500">
              {desiredLanguage !== 'auto' && desiredLanguage !== language ? (
                <span className="text-violet-400 font-medium flex items-center gap-1">
                  <Sparkles className="w-3 h-3 shrink-0" />
                  Transcribes and translates output into {DESIRED_LANGUAGES.find(l => l.code === desiredLanguage)?.name || desiredLanguage}
                </span>
              ) : (
                'Target script/language for the final transcript.'
              )}
            </p>
          </div>

        </div>

        {/* Diarization Toggle */}
        <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
          <div className="space-y-0.5">
            <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
              <Users className="w-3.5 h-3.5 text-pink-400" />
              <span>Speaker Diarization</span>
            </label>
            <span className="text-xs text-slate-400">
              Separate distinct speakers in meetings & interviews (Speaker 1, Speaker 2)
            </span>
          </div>

          <label className="relative inline-flex items-center cursor-pointer select-none shrink-0 ml-4">
            <input
              type="checkbox"
              checked={diarize}
              onChange={(e) => setDiarize(e.target.checked)}
              disabled={isProcessing}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-brand-500 peer-checked:to-violet-600"></div>
          </label>
        </div>

      </div>

      {/* API Key Missing Alert */}
      {isApiKeyMissing && (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between gap-4 text-xs text-amber-300">
          <div className="flex items-center gap-3">
            <Key className="w-5 h-5 text-amber-400 shrink-0" />
            <div>
              <div className="font-bold text-amber-200">Cloud API Key Required</div>
              <div className="text-slate-400 text-[11px]">An API key is required in <code>backend/.env</code> to transcribe via Cloud API.</div>
            </div>
          </div>
          <button
            type="button"
            onClick={onOpenSettings}
            className="px-3.5 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shrink-0 transition-colors shadow-md shadow-amber-500/20"
          >
            Configure Key
          </button>
        </div>
      )}

      {/* Model Loading Note (if local model is still loading in background) */}
      {provider === 'local' && !modelReady && (
        <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center gap-3 text-xs text-amber-300">
          <Info className="w-4 h-4 shrink-0 text-amber-400 animate-pulse" />
          <span>
            <strong>First Load Notice:</strong> Whisper Large-v3 Turbo model is initializing on your system. You can queue your transcription now; it will begin automatically once loaded.
          </span>
        </div>
      )}

      {/* Error Message banner */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-start gap-3 text-xs text-rose-300">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
          <div>
            <div className="font-semibold mb-0.5">Transcription failed</div>
            <div>{errorMessage}</div>
          </div>
        </div>
      )}

      {/* Progress Stages (visible when processing) */}
      {isProcessing && (
        <ProgressStages
          stage={currentStage}
          progress={progress}
          diarize={diarize}
          desiredLanguage={desiredLanguage}
          language={language}
          provider={jobData?.provider || provider}
          modelName={
            jobData?.model_name ||
            (provider === 'api'
              ? (settingsInfo?.api_model || 'whisper-1')
              : 'Whisper Large-v3 Turbo')
          }
        />
      )}

      {/* Action Button */}
      {!isProcessing && (
        <div className="pt-2">
          <button
            onClick={handleSubmit}
            disabled={!hasInput || isProcessing}
            className={`w-full py-4 px-6 rounded-2xl font-bold text-base flex items-center justify-center gap-2.5 transition-all shadow-xl ${
              hasInput
                ? isApiKeyMissing
                  ? 'bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-amber-500/20 cursor-pointer'
                  : 'bg-gradient-to-r from-brand-600 via-violet-600 to-pink-600 hover:from-brand-500 hover:via-violet-500 hover:to-pink-500 text-white shadow-brand-500/25 cursor-pointer transform hover:-translate-y-0.5 active:translate-y-0'
                : 'bg-slate-800 text-slate-500 border border-slate-700/60 cursor-not-allowed opacity-60'
            }`}
          >
            <Sparkles className="w-5 h-5 text-brand-300" />
            <span>
              {isApiKeyMissing
                ? 'Configure API Key to Transcribe'
                : isRecordingTab
                ? `Transcribe Recording (${provider === 'api' ? 'Cloud API' : 'Local Turbo'})`
                : activeTab === 'video'
                ? `Extract Audio & Transcribe Video (${provider === 'api' ? 'Cloud API' : 'Local Turbo'})`
                : `Transcribe Audio (${provider === 'api' ? 'Cloud API' : 'Local Turbo'})`}
            </span>
          </button>
        </div>
      )}

    </div>
  );
}
