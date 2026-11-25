import { useState, useEffect, useRef, useCallback } from 'react';
import { getJobStatus } from '../api/client';

export function useJobPolling() {
  const [jobId, setJobId] = useState(null);
  const [jobData, setJobData] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const timerRef = useRef(null);

  const startPolling = useCallback((newJobId) => {
    setJobId(newJobId);
    setJobData({
      job_id: newJobId,
      status: 'pending',
      stage: 'uploading',
      progress: 10,
      result: null,
      error: null
    });
    setIsPolling(true);
  }, []);

  const stopPolling = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const resetJob = useCallback(() => {
    stopPolling();
    setJobId(null);
    setJobData(null);
  }, [stopPolling]);

  useEffect(() => {
    if (!jobId || !isPolling) return;

    let consecutiveErrors = 0;

    const poll = async () => {
      try {
        const data = await getJobStatus(jobId);
        setJobData(data);
        consecutiveErrors = 0;

        if (data.status === 'completed' || data.status === 'failed') {
          stopPolling();
        }
      } catch (err) {
        consecutiveErrors += 1;
        console.warn(`Polling error (${consecutiveErrors}):`, err);
        if (consecutiveErrors >= 10) {
          setJobData(prev => ({
            ...prev,
            status: 'failed',
            stage: 'failed',
            error: 'Server disconnected or connection lost.'
          }));
          stopPolling();
        }
      }
    };

    poll();
    timerRef.current = setInterval(poll, 1200);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [jobId, isPolling, stopPolling]);

  return {
    jobId,
    jobData,
    isPolling,
    startPolling,
    stopPolling,
    resetJob
  };
}
