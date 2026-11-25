import React, { useState, useEffect } from 'react';
import { getHistory, getHistoryDetail, deleteHistoryItem } from '../api/client';
import { HistoryItem } from '../components/HistoryItem';
import { TranscriptModal } from '../components/TranscriptModal';
import { Search, Loader2, FileX2, RefreshCw } from 'lucide-react';

export function History({ onShowToast, onNavigateHome }) {
  const [historyList, setHistoryList] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedTranscript, setSelectedTranscript] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const fetchHistory = async (searchTerm = '') => {
    setLoading(true);
    try {
      const data = await getHistory(searchTerm);
      setHistoryList(data);
    } catch (err) {
      onShowToast({ type: 'error', message: 'Failed to load history.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      fetchHistory(search);
    }, 300);
    return () => clearTimeout(delayDebounce);
  }, [search]);

  const handleView = async (id) => {
    setLoadingDetail(true);
    try {
      const detail = await getHistoryDetail(id);
      setSelectedTranscript(detail);
      setModalOpen(true);
    } catch (err) {
      onShowToast({ type: 'error', message: 'Failed to load transcript detail.' });
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteHistoryItem(id);
      setHistoryList(prev => prev.filter(item => item.id !== id));
      onShowToast({ type: 'success', message: 'Transcript deleted from history.' });
    } catch (err) {
      onShowToast({ type: 'error', message: 'Failed to delete transcript.' });
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-8 animate-fade-in">
      
      {/* Header and Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Transcript History
          </h2>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            All your local speech recognition transcripts stored securely on this machine.
          </p>
        </div>

        {/* Search Input */}
        <div className="flex items-center gap-3 w-full sm:w-80">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search transcripts..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/50 transition-all placeholder:text-slate-500"
            />
          </div>
          <button
            onClick={() => fetchHistory(search)}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-700/80 text-slate-400 hover:text-white transition-colors"
            title="Refresh history"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* History Content */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400">
          <Loader2 className="w-8 h-8 animate-spin text-brand-400 mb-3" />
          <p className="text-sm">Loading transcript history...</p>
        </div>
      ) : historyList.length === 0 ? (
        <div className="p-12 rounded-3xl bg-slate-900/40 border border-slate-800/80 text-center flex flex-col items-center justify-center">
          <div className="w-16 h-16 rounded-2xl bg-slate-800/60 border border-slate-700/60 flex items-center justify-center text-slate-400 mb-4">
            <FileX2 className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-semibold text-slate-200 mb-1">
            {search ? 'No matching transcripts found' : 'No transcripts yet'}
          </h3>
          <p className="text-xs text-slate-400 max-w-sm mb-6">
            {search
              ? 'Try modifying your search term or clear the filter.'
              : 'Transcribe your first audio file, video, or browser recording to see it here.'}
          </p>
          {!search && (
            <button
              onClick={onNavigateHome}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-brand-600 to-violet-600 text-white text-sm font-semibold shadow-lg shadow-brand-500/20 hover:scale-105 transition-all"
            >
              Start Transcribing
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {historyList.map((item) => (
            <HistoryItem
              key={item.id}
              item={item}
              onView={handleView}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Transcript Detail Modal */}
      <TranscriptModal
        transcript={selectedTranscript}
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
      />

    </div>
  );
}
