import React, { useState, useEffect } from 'react';
import { TranscribeCard } from '../components/TranscribeCard';
import { TranscriptViewer } from '../components/TranscriptViewer';
import { useRecorder } from '../hooks/useRecorder';
import { useJobPolling } from '../hooks/useJobPolling';
import { submitTranscription } from '../api/client';
import { Sparkles, ShieldCheck, Zap, HardDrive, Cloud, Cpu, Globe } from 'lucide-react';

export function Home({ healthInfo, settingsInfo, onOpenSettings, onSettingsUpdated, onShowToast }) {
  const [activeTab, setActiveTab] = useState('audio'); // 'audio' | 'video' | 'record'
  const [selectedFile, setSelectedFile] = useState(null);
  const [diarize, setDiarize] = useState(false);
  const [language, setLanguage] = useState('auto');
  const [desiredLanguage, setDesiredLanguage] = useState('auto');
  const [provider, setProvider] = useState(settingsInfo?.transcription_mode || 'local');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState(null);
  const [transcriptResult, setTranscriptResult] = useState(null);

  const recorder = useRecorder();
  const { jobData, isPolling, startPolling, resetJob } = useJobPolling();

  // Sync provider with settings when loaded
  useEffect(() => {
    if (settingsInfo?.transcription_mode) {
      setProvider(settingsInfo.transcription_mode);
    }
  }, [settingsInfo?.transcription_mode]);

  const isProcessing = isSubmitting || isPolling;
  const currentStage = jobData?.stage || (isSubmitting ? 'uploading' : 'idle');
  const progress = jobData?.progress || (isSubmitting ? 10 : 0);

  // When job completes, store result
  useEffect(() => {
    if (jobData?.status === 'completed' && jobData?.result) {
      setTranscriptResult(jobData.result);
      onShowToast({ type: 'success', message: 'Transcription completed successfully!' });
      resetJob();
    } else if (jobData?.status === 'failed') {
      setSubmissionError(jobData.error || 'Transcription job failed.');
      onShowToast({ type: 'error', message: jobData.error || 'Transcription failed.' });
      resetJob();
    }
  }, [jobData, onShowToast, resetJob]);

  const handleSubmit = async (fileToSubmit, sourceType, chosenProvider) => {
    setIsSubmitting(true);
    setSubmissionError(null);
    setTranscriptResult(null);

    try {
      const response = await submitTranscription({
        file: fileToSubmit,
        sourceType,
        diarize,
        language,
        desiredLanguage,
        provider: chosenProvider || provider,
      });

      startPolling(response.job_id);
    } catch (err) {
      setSubmissionError(err.message || 'Failed to submit transcription.');
      onShowToast({ type: 'error', message: err.message || 'Submission failed' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetForNew = () => {
    setTranscriptResult(null);
    setSelectedFile(null);
    recorder.resetRecording();
    setSubmissionError(null);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-10">
      
      {/* Dynamic Hero Section */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/20 text-xs font-semibold text-brand-400 mb-2">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Dual-Engine Speech Recognition &bull; Local &amp; Cloud</span>
        </div>
        
        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white">
          Accurate Speech to Text, <span className="gradient-text">Your Way</span>
        </h1>
        
        <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Transcribe audio, extract speech from video, separate speakers, and translate output using either 100% offline local Whisper or lightning-fast cloud APIs.
        </p>

        {/* Feature Pills */}
        <div className="flex items-center justify-center gap-3 sm:gap-6 pt-2 text-xs text-slate-400 flex-wrap">
          <span className="flex items-center gap-1.5 bg-slate-900/60 px-3 py-1 rounded-full border border-slate-800">
            <Cpu className="w-4 h-4 text-brand-400" />
            100% Offline Local Model
          </span>
          <span className="flex items-center gap-1.5 bg-slate-900/60 px-3 py-1 rounded-full border border-slate-800">
            <Cloud className="w-4 h-4 text-violet-400" />
            Instant Cloud API
          </span>
          <span className="flex items-center gap-1.5 bg-slate-900/60 px-3 py-1 rounded-full border border-slate-800">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Private &amp; Secure
          </span>
          <span className="flex items-center gap-1.5 bg-slate-900/60 px-3 py-1 rounded-full border border-slate-800">
            <Globe className="w-4 h-4 text-pink-400" />
            Multi-Language
          </span>
        </div>
      </div>

      {/* Main Workflow: Form or Result */}
      {transcriptResult ? (
        <TranscriptViewer
          result={transcriptResult}
          onNewTranscription={handleResetForNew}
        />
      ) : (
        <TranscribeCard
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          selectedFile={selectedFile}
          setSelectedFile={setSelectedFile}
          recorder={recorder}
          diarize={diarize}
          setDiarize={setDiarize}
          language={language}
          setLanguage={setLanguage}
          desiredLanguage={desiredLanguage}
          setDesiredLanguage={setDesiredLanguage}
          provider={provider}
          setProvider={setProvider}
          settingsInfo={settingsInfo}
          onOpenSettings={onOpenSettings}
          onSubmit={handleSubmit}
          isProcessing={isProcessing}
          currentStage={currentStage}
          progress={progress}
          jobData={jobData}
          modelReady={healthInfo?.model_ready}
          errorMessage={submissionError}
        />
      )}

    </div>
  );
}
