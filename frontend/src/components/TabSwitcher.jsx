import React from 'react';
import { Music, Video, Mic } from 'lucide-react';

export function TabSwitcher({ activeTab, onChangeTab, disabled }) {
  const tabs = [
    { id: 'audio', label: 'Upload Audio', icon: Music },
    { id: 'video', label: 'Upload Video', icon: Video },
    { id: 'record', label: 'Record Live', icon: Mic },
  ];

  return (
    <div className="flex p-1.5 rounded-2xl bg-slate-800/60 dark:bg-slate-900/80 border border-slate-700/60 backdrop-blur-md">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;

        return (
          <button
            key={tab.id}
            disabled={disabled}
            onClick={() => onChangeTab(tab.id)}
            className={`flex-1 flex items-center justify-center gap-2.5 py-3 px-4 rounded-xl text-sm font-semibold transition-all duration-200 select-none ${
              isActive
                ? 'bg-gradient-to-r from-brand-600 to-violet-600 text-white shadow-lg shadow-brand-500/25 scale-[1.01]'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/30'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
            <span>{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}
