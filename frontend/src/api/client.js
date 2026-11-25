const API_BASE = '/api';

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function submitTranscription({ file, sourceType, diarize, language, desiredLanguage, provider }) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source_type', sourceType);
  formData.append('diarize', diarize ? 'true' : 'false');
  formData.append('language', language || 'auto');
  formData.append('desired_language', desiredLanguage || 'auto');
  if (provider) {
    formData.append('provider', provider);
  }

  const res = await fetch(`${API_BASE}/transcribe`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    let errDetail = 'Failed to submit transcription job';
    try {
      const errJson = await res.json();
      if (errJson.detail) errDetail = errJson.detail;
    } catch {
      errDetail = res.statusText || errDetail;
    }
    throw new Error(errDetail);
  }

  return res.json(); // { job_id, status, message }
}

export async function getSettings() {
  const res = await fetch(`${API_BASE}/settings`);
  if (!res.ok) {
    throw new Error(`Failed to fetch settings: ${res.statusText}`);
  }
  return res.json();
}

export async function updateSettings(settingsData) {
  const res = await fetch(`${API_BASE}/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settingsData),
  });

  if (!res.ok) {
    let errDetail = 'Failed to update settings';
    try {
      const errJson = await res.json();
      if (errJson.detail) errDetail = errJson.detail;
    } catch {
      errDetail = res.statusText || errDetail;
    }
    throw new Error(errDetail);
  }
  return res.json();
}

export async function testApiKey(testData = {}) {
  const res = await fetch(`${API_BASE}/settings/test-api`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(testData),
  });

  if (!res.ok) {
    throw new Error(`API test failed: ${res.statusText}`);
  }
  return res.json(); // { success, message, details }
}

export async function getJobStatus(jobId) {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch job status: ${res.statusText}`);
  }
  return res.json();
}

export async function getHistory(search = '') {
  const query = search ? `?search=${encodeURIComponent(search)}` : '';
  const res = await fetch(`${API_BASE}/history${query}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch history: ${res.statusText}`);
  }
  return res.json();
}

export async function getHistoryDetail(id) {
  const res = await fetch(`${API_BASE}/history/${id}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch transcript details: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteHistoryItem(id) {
  const res = await fetch(`${API_BASE}/history/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error(`Failed to delete transcript: ${res.statusText}`);
  }
  return res.json();
}

export function getDownloadUrl(id, format = 'txt') {
  return `${API_BASE}/history/${id}/download?format=${format}`;
}
