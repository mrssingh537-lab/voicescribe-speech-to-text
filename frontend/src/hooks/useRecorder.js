import { useState, useRef, useEffect, useCallback } from 'react';

export function useRecorder() {
  const [state, setState] = useState('idle'); // 'idle' | 'recording' | 'paused' | 'stopped'
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [audioLevels, setAudioLevels] = useState([20, 20, 20, 20, 20, 20, 20, 20]);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const timerIntervalRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animFrameRef = useRef(null);

  const cleanupAudioNodes = () => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };

  const startVisualizer = (stream) => {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioCtx();
      audioContextRef.current = audioCtx;
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyserRef.current = analyser;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      const updateWaveform = () => {
        if (analyserRef.current) {
          analyserRef.current.getByteFrequencyData(dataArray);
          // Pick 12 bins for wave animation
          const sampled = [];
          const step = Math.floor(dataArray.length / 12) || 1;
          for (let i = 0; i < 12; i++) {
            const val = dataArray[i * step] || 10;
            // Map 0..255 to percentage height 10%..100%
            sampled.push(Math.max(10, Math.min(100, Math.round((val / 255) * 100))));
          }
          setAudioLevels(sampled);
        }
        animFrameRef.current = requestAnimationFrame(updateWaveform);
      };
      updateWaveform();
    } catch (e) {
      console.warn('AudioContext visualizer not supported or failed:', e);
    }
  };

  const startRecording = useCallback(async () => {
    cleanupAudioNodes();
    audioChunksRef.current = [];
    setAudioBlob(null);
    setAudioUrl(null);
    setElapsedSeconds(0);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Choose supported mimeType
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : MediaRecorder.isTypeSupported('audio/mp4')
          ? 'audio/mp4'
          : '';
      }

      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const finalBlob = new Blob(audioChunksRef.current, {
          type: mimeType || 'audio/webm'
        });
        setAudioBlob(finalBlob);
        const url = URL.createObjectURL(finalBlob);
        setAudioUrl(url);
        setState('stopped');
        clearInterval(timerIntervalRef.current);
        cleanupAudioNodes();
      };

      recorder.start(250); // collect data every 250ms
      setState('recording');
      startVisualizer(stream);

      timerIntervalRef.current = setInterval(() => {
        setElapsedSeconds(prev => prev + 1);
      }, 1000);

    } catch (err) {
      console.error('Failed to access microphone:', err);
      throw err;
    }
  }, []);

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && state === 'recording') {
      mediaRecorderRef.current.pause();
      setState('paused');
      clearInterval(timerIntervalRef.current);
    }
  }, [state]);

  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && state === 'paused') {
      mediaRecorderRef.current.resume();
      setState('recording');
      timerIntervalRef.current = setInterval(() => {
        setElapsedSeconds(prev => prev + 1);
      }, 1000);
    }
  }, [state]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && (state === 'recording' || state === 'paused')) {
      mediaRecorderRef.current.stop();
    }
  }, [state]);

  const resetRecording = useCallback(() => {
    cleanupAudioNodes();
    clearInterval(timerIntervalRef.current);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    setState('idle');
    setElapsedSeconds(0);
    setAudioBlob(null);
    setAudioUrl(null);
    setAudioLevels([20, 20, 20, 20, 20, 20, 20, 20]);
  }, [audioUrl]);

  useEffect(() => {
    return () => {
      cleanupAudioNodes();
      clearInterval(timerIntervalRef.current);
    };
  }, []);

  return {
    state,
    isRecording: state === 'recording',
    isPaused: state === 'paused',
    isStopped: state === 'stopped',
    elapsedSeconds,
    audioBlob,
    audioUrl,
    audioLevels,
    startRecording,
    pauseRecording,
    resumeRecording,
    stopRecording,
    resetRecording,
  };
}
