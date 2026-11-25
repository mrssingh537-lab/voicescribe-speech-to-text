import React from 'react';
import { Waves, Cpu, Cloud, Settings as SettingsIcon, Sparkles } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';

export function Navbar({ currentPage, onNavigate, healthInfo, settingsInfo, onOpenSettings, isDark, onToggleTheme }) {
  const isApiMode = (settingsInfo?.transcription_mode || healthInfo?.transcription_mode) === 'api';
  const isModelReady = healthInfo?.model_ready;
  const device = healthInfo?.device?.toUpperCase() || 'CPU';
  const modelName = healthInfo?.model_name || (isApiMode ? 'API' : 'Turbo');

  const navItems = [
    { id: 'home', label: 'Home' },
    { id: 'history', label: 'History' },
    { id: 'about', label: 'About' },
  ];

  return (
    <header className="sticky top-0 z-40 backdrop-blur-xl bg-slate-900/70 dark:bg-slate-950/70 border-b border-slate-800/80 transition-colors">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        
        {/* Brand */}
        <div 
          onClick={() => onNavigate('home')}
          className="flex items-center gap-3 cursor-pointer group select-none"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 via-brand-500 to-violet-500 p-0.5 shadow-lg shadow-brand-500/20 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <Waves className="w-5 h-5 text-brand-400 group-hover:text-brand-300 transition-colors" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-lg tracking-tight text-white">VoiceScribe</span>
              <span className={`text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded-full border ${
                isApiMode 
                  ? 'bg-violet-500/10 text-violet-400 border-violet-500/20'
                  : 'bg-brand-500/10 text-brand-400 border-brand-500/20'
              }`}>
                {isApiMode ? 'Cloud API' : 'Turbo'}
              </span>
            </div>
          </div>
        </div>

        {/* Center Nav Links */}
        <nav className="flex items-center gap-1 bg-slate-800/40 p-1 rounded-xl border border-slate-800/60">
          {navItems.map((item) => {
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-brand-600 text-white shadow-md shadow-brand-600/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Right Section: Provider Status Badge + Settings + Theme Toggle */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Health / Provider Status Badge */}
          <button 
            onClick={onOpenSettings}
            type="button"
            className={`hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium border transition-transform hover:scale-105 cursor-pointer ${
              isApiMode
                ? settingsInfo?.api_key_configured
                  ? 'bg-violet-500/10 border-violet-500/30 text-violet-300 hover:bg-violet-500/20'
                  : 'bg-amber-500/10 border-amber-500/30 text-amber-300 hover:bg-amber-500/20'
                : isModelReady
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
                  : 'bg-amber-500/10 border-amber-500/30 text-amber-400 hover:bg-amber-500/20'
            }`}
            title="Click to configure Local vs Cloud API transcription mode"
          >
            <span className={`w-2 h-2 rounded-full ${
              (isApiMode ? settingsInfo?.api_key_configured : isModelReady) 
                ? 'bg-emerald-400 animate-pulse' 
                : 'bg-amber-400 animate-ping'
            }`} />
            {isApiMode ? <Cloud className="w-3.5 h-3.5 text-violet-400" /> : <Cpu className="w-3.5 h-3.5 text-brand-400" />}
            <span>
              {isApiMode
                ? settingsInfo?.api_key_configured ? `API (${settingsInfo?.api_model || 'whisper-1'})` : 'API: Key Required'
                : isModelReady ? `Whisper (${device})` : 'Loading Local...'}
            </span>
          </button>

          {/* Quick Settings Button */}
          <button
            onClick={onOpenSettings}
            type="button"
            title="Provider & API Settings"
            className="p-2 rounded-xl text-slate-400 hover:text-white bg-slate-800/50 hover:bg-slate-800 border border-slate-700/60 transition-colors"
          >
            <SettingsIcon className="w-4 h-4" />
          </button>

          <ThemeToggle isDark={isDark} onToggle={onToggleTheme} />
        </div>

      </div>
    </header>
  );
}
