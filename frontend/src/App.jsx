import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Toast } from './components/Toast';
import { SettingsModal } from './components/SettingsModal';
import { Home } from './pages/Home';
import { History } from './pages/History';
import { About } from './pages/About';
import { useTheme } from './hooks/useTheme';
import { getHealth, getSettings } from './api/client';

export function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [healthInfo, setHealthInfo] = useState(null);
  const [settingsInfo, setSettingsInfo] = useState(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [toast, setToast] = useState(null);
  const { isDark, toggleTheme } = useTheme();

  const showToast = (toastData) => {
    setToast(toastData);
    setTimeout(() => {
      setToast((current) => (current === toastData ? null : current));
    }, 4500);
  };

  const checkHealth = async () => {
    try {
      const data = await getHealth();
      setHealthInfo(data);
    } catch (e) {
      console.warn('Backend health check error:', e);
    }
  };

  const checkSettings = async () => {
    try {
      const data = await getSettings();
      setSettingsInfo(data);
    } catch (e) {
      console.warn('Backend settings check error:', e);
    }
  };

  useEffect(() => {
    checkHealth();
    checkSettings();

    // Poll health until model or API is ready
    const interval = setInterval(async () => {
      try {
        const data = await getHealth();
        setHealthInfo(data);
        if (data.model_ready) {
          clearInterval(interval);
        }
      } catch (err) {
        // backend might still be starting
      }
    }, 2500);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 selection:bg-brand-500 selection:text-white">
      {/* Navigation */}
      <Navbar
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        healthInfo={healthInfo}
        settingsInfo={settingsInfo}
        onOpenSettings={() => setIsSettingsOpen(true)}
        isDark={isDark}
        onToggleTheme={toggleTheme}
      />

      {/* Main Page Content */}
      <main className="flex-1">
        {currentPage === 'home' && (
          <Home
            healthInfo={healthInfo}
            settingsInfo={settingsInfo}
            onOpenSettings={() => setIsSettingsOpen(true)}
            onSettingsUpdated={(updated) => {
              setSettingsInfo(updated);
              checkHealth();
            }}
            onShowToast={showToast}
          />
        )}
        {currentPage === 'history' && (
          <History
            onShowToast={showToast}
            onNavigateHome={() => setCurrentPage('home')}
          />
        )}
        {currentPage === 'about' && (
          <About />
        )}
      </main>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        currentSettings={settingsInfo}
        onSettingsUpdated={(updated) => {
          setSettingsInfo(updated);
          checkHealth();
        }}
        onShowToast={showToast}
      />

      {/* Footer */}
      <footer className="border-t border-slate-900/80 py-6 text-center text-xs text-slate-500">
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            VoiceScribe &bull; Dual-Engine Speech-to-Text (Offline Whisper &amp; Cloud API)
          </div>
          <div>
            Powered by Whisper Large-v3 Turbo &bull; OpenAI API &bull; PyTorch &bull; FastAPI &bull; React
          </div>
        </div>
      </footer>

      {/* Toast Notification Container */}
      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  );
}

export default App;
