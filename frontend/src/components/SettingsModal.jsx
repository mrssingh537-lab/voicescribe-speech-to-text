import React, { useState, useEffect } from 'react';
import { 
  X, 
  Cpu, 
  Cloud, 
  Key, 
  Server, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Eye, 
  EyeOff, 
  Sparkles,
  ShieldCheck,
  Zap,
  ExternalLink
} from 'lucide-react';
import { testApiKey, updateSettings } from '../api/client';

export function SettingsModal({ isOpen, onClose, currentSettings, onSettingsUpdated, onShowToast }) {
  const [mode, setMode] = useState('local');
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [apiUrl, setApiUrl] = useState('https://api.openai.com/v1/audio/transcriptions');
  const [apiModel, setApiModel] = useState('whisper-1');
  
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState(null); // { success: bool, message: string }
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (currentSettings) {
      setMode(currentSettings.transcription_mode || 'local');
      setApiUrl(currentSettings.api_url || 'https://api.openai.com/v1/audio/transcriptions');
      setApiModel(currentSettings.api_model || 'whisper-1');
      setTestResult(null);
      setApiKey(''); // Keep input blank unless user enters a new key
    }
  }, [currentSettings, isOpen]);

  if (!isOpen) return null;

  const handleSelectPreset = (preset) => {
    if (preset === 'openai') {
      setApiUrl('https://api.openai.com/v1/audio/transcriptions');
      setApiModel('whisper-1');
    } else if (preset === 'groq') {
      setApiUrl('https://api.groq.com/openai/v1/audio/transcriptions');
      setApiModel('whisper-large-v3-turbo');
    } else if (preset === 'gpt-transcribe') {
      setApiUrl('https://api.openai.com/v1/audio/transcriptions');
      setApiModel('gpt-transcribe');
    }
  };

  const handleTestKey = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await testApiKey({
        api_key: apiKey || undefined,
        api_url: apiUrl,
        api_model: apiModel,
      });
      setTestResult(res);
      if (res.success) {
        onShowToast?.({ type: 'success', message: 'API connection verified successfully!' });
      } else {
        onShowToast?.({ type: 'error', message: res.message || 'API verification failed' });
      }
    } catch (err) {
      setTestResult({
        success: false,
        message: err.message || 'Network test failed. Check your connection.'
      });
      onShowToast?.({ type: 'error', message: err.message || 'Connection failed' });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      const payload = {
        transcription_mode: mode,
        api_url: apiUrl,
        api_model: apiModel,
      };
      if (apiKey.trim()) {
        payload.api_key = apiKey.trim();
      }

      const updated = await updateSettings(payload);
      onSettingsUpdated?.(updated);
      onShowToast?.({ 
        type: 'success', 
        message: `Mode set to ${mode.toUpperCase()} and settings saved in backend/.env` 
      });
      onClose();
    } catch (err) {
      onShowToast?.({ type: 'error', message: err.message || 'Failed to save settings' });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div 
        className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-800/80 flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Transcription Provider Settings</h3>
              <p className="text-xs text-slate-400">Choose between local offline Whisper and cloud API providers</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="p-6 space-y-6 overflow-y-auto custom-scrollbar">
          
          {/* Provider Selection Cards */}
          <div className="space-y-3">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block">
              Active Transcription Mode
            </label>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              {/* Local Option */}
              <div 
                onClick={() => setMode('local')}
                className={`p-4 rounded-2xl border cursor-pointer transition-all relative select-none flex flex-col justify-between ${
                  mode === 'local'
                    ? 'bg-brand-500/10 border-brand-500/60 ring-2 ring-brand-500/20'
                    : 'bg-slate-950/40 border-slate-800 hover:border-slate-700 hover:bg-slate-800/30'
                }`}
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-brand-400">
                      <Cpu className="w-5 h-5" />
                      <span className="font-bold text-white">Local Whisper</span>
                    </div>
                    {mode === 'local' && (
                      <span className="w-2.5 h-2.5 rounded-full bg-brand-400 animate-pulse" />
                    )}
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Whisper Large-v3 Turbo running offline on your local GPU/CPU. 100% private with zero external API calls.
                  </p>
                </div>

                <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">Model: Large-v3 Turbo</span>
                  <span className="text-emerald-400 font-semibold flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" /> 100% Offline
                  </span>
                </div>
              </div>

              {/* Cloud API Option */}
              <div 
                onClick={() => setMode('api')}
                className={`p-4 rounded-2xl border cursor-pointer transition-all relative select-none flex flex-col justify-between ${
                  mode === 'api'
                    ? 'bg-violet-500/10 border-violet-500/60 ring-2 ring-violet-500/20'
                    : 'bg-slate-950/40 border-slate-800 hover:border-slate-700 hover:bg-slate-800/30'
                }`}
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-violet-400">
                      <Cloud className="w-5 h-5" />
                      <span className="font-bold text-white">Cloud Whisper API</span>
                    </div>
                    {mode === 'api' && (
                      <span className="w-2.5 h-2.5 rounded-full bg-violet-400 animate-pulse" />
                    )}
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    High-speed cloud transcription via OpenAI or Groq Whisper. Minimal local CPU/RAM load, handles large files fast.
                  </p>
                </div>

                <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">Requires API Key</span>
                  <span className="text-amber-400 font-semibold flex items-center gap-1">
                    <Zap className="w-3.5 h-3.5" /> Lightning Fast
                  </span>
                </div>
              </div>

            </div>
          </div>

          {/* Cloud API Configuration Section */}
          <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-4">
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-violet-400" />
                <h4 className="font-bold text-white text-sm">Cloud API Configuration</h4>
              </div>

              {/* Quick Presets */}
              <div className="flex items-center gap-1.5 text-xs">
                <span className="text-slate-500 text-[11px] mr-1 hidden sm:inline">Presets:</span>
                <button
                  type="button"
                  onClick={() => handleSelectPreset('openai')}
                  className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700/60 transition-colors"
                >
                  OpenAI
                </button>
                <button
                  type="button"
                  onClick={() => handleSelectPreset('groq')}
                  className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700/60 transition-colors"
                >
                  Groq
                </button>
                <button
                  type="button"
                  onClick={() => handleSelectPreset('gpt-transcribe')}
                  className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-[11px] font-medium border border-slate-700/60 transition-colors"
                >
                  GPT-Transcribe
                </button>
              </div>
            </div>

            {/* API Key Input */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-300">
                  API Key
                </label>
                {currentSettings?.api_key_configured && (
                  <span className="text-[11px] text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    Key stored ({currentSettings.api_key_masked})
                  </span>
                )}
              </div>

              <div className="relative">
                <input
                  type={showKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={
                    currentSettings?.api_key_configured
                      ? `Leave blank to keep current key (${currentSettings.api_key_masked})`
                      : 'sk-proj-...'
                  }
                  className="w-full pl-3.5 pr-24 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all font-mono placeholder:text-slate-500"
                />

                <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800 transition-colors"
                    title={showKey ? 'Hide key' : 'Show key'}
                  >
                    {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                  <button
                    type="button"
                    onClick={handleTestKey}
                    disabled={isTesting || (!apiKey && !currentSettings?.api_key_configured)}
                    className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-violet-600/30 hover:bg-violet-600/50 text-violet-300 border border-violet-500/30 disabled:opacity-40 transition-colors flex items-center gap-1"
                  >
                    {isTesting ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Test'}
                  </button>
                </div>
              </div>

              <p className="text-[11px] text-slate-500">
                Key will be stored in <code className="text-slate-400 bg-slate-800/80 px-1 py-0.5 rounded">backend/.env</code> on your computer.
              </p>
            </div>

            {/* Test Result Feedback */}
            {testResult && (
              <div 
                className={`p-3 rounded-xl border flex items-start gap-2.5 text-xs animate-fade-in ${
                  testResult.success
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                }`}
              >
                {testResult.success ? (
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
                )}
                <div>
                  <span className="font-semibold">{testResult.success ? 'Success: ' : 'Test Failed: '}</span>
                  {testResult.message}
                </div>
              </div>
            )}

            {/* Endpoint & Model Settings */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-400">
                  Endpoint URL
                </label>
                <input
                  type="text"
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700/80 text-slate-200 text-xs focus:outline-none focus:ring-1 focus:ring-violet-500/50 font-mono"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-400">
                  Model Identifier
                </label>
                <input
                  type="text"
                  value={apiModel}
                  onChange={(e) => setApiModel(e.target.value)}
                  placeholder="whisper-1"
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700/80 text-slate-200 text-xs focus:outline-none focus:ring-1 focus:ring-violet-500/50 font-mono"
                />
              </div>
            </div>

          </div>

        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800/80 bg-slate-950/40 flex items-center justify-between gap-3">
          <div className="text-xs text-slate-500 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Settings saved automatically to backend/.env</span>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={onClose}
              disabled={isSaving}
              className="px-4 py-2 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving}
              className="px-5 py-2 rounded-xl text-sm font-semibold bg-gradient-to-r from-brand-600 to-violet-600 hover:from-brand-500 hover:to-violet-500 text-white shadow-lg shadow-brand-500/25 flex items-center gap-2 transition-all"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-brand-300" />
                  <span>Save & Apply</span>
                </>
              )}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
