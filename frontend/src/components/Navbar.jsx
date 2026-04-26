import React from 'react';
import { Box, ExternalLink, RefreshCw, Smartphone, CheckCircle2 } from 'lucide-react';

const Navbar = ({ onReset, installPrompt, onInstall, isStandalone, alreadyInstalled }) => {
  return (
    <nav className="glass sticky top-0 z-50 border-b border-white/5 px-4 sm:px-8 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3 sm:gap-4">
          <div className="bg-indigo-600 p-2 sm:p-2.5 rounded-xl shadow-lg shadow-indigo-600/20">
            <Box className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg sm:text-2xl font-black tracking-tight text-white flex items-center">
              STAAD<span className="text-indigo-500">Procure</span>
            </h1>
            <p className="hidden sm:block text-[10px] text-slate-500 font-black uppercase tracking-[0.2em] leading-none mt-1">
              Material Analysis API
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-4">
          <a 
            href="http://localhost:8000/docs" 
            target="_blank" 
            rel="noopener noreferrer"
            className="hidden sm:flex items-center gap-2 text-sm font-bold text-slate-400 hover:text-white transition-colors mr-2 sm:mr-4"
          >
            Docs
            <ExternalLink className="w-3 h-3" />
          </a>
          
          {isStandalone ? (
            <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] sm:text-xs font-bold uppercase tracking-widest">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span className="hidden xs:inline">System Active</span>
              <span className="xs:hidden">App</span>
            </div>
          ) : alreadyInstalled ? (
            <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] sm:text-xs font-bold uppercase tracking-widest">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span className="hidden xs:inline">App Installed</span>
              <span className="xs:hidden">Installed</span>
            </div>
          ) : installPrompt ? (
            <button 
              onClick={onInstall}
              className="flex items-center gap-2 text-xs sm:text-sm font-bold px-4 sm:px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-lg shadow-indigo-600/20 group animate-in fade-in slide-in-from-top-1"
            >
              <Smartphone className="w-4 h-4 transition-transform group-hover:scale-110" />
              <span className="hidden sm:inline">Install App</span>
              <span className="sm:hidden">Install</span>
            </button>
          ) : null}

          <button 
            onClick={onReset}
            className="flex items-center gap-2 text-xs sm:text-sm font-bold px-4 sm:px-5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-slate-200 transition-all border border-white/5"
          >
            <RefreshCw className="w-4 h-4 sm:hidden" />
            <span className="hidden sm:inline">Start Fresh</span>
            <span className="sm:hidden">Reset</span>
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
