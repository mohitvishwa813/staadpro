import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FileUp, 
  FileSpreadsheet, 
  BarChart3, 
  Table as TableIcon, 
  Download, 
  RefreshCw,
  Search,
  CheckCircle2,
  AlertCircle,
  Layers,
  ArrowRight
} from 'lucide-react';
import Navbar from './components/Navbar';
import FileUpload from './components/FileUpload';
import StatsGrid from './components/StatsGrid';
import ResultsTable from './components/ResultsTable';

const API_BASE = 'http://localhost:8000';

function App() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [view, setView] = useState('summary'); // 'summary' | 'detail' | 'parts'

  const resetApp = () => {
    setFile(null);
    setData(null);
    setError(null);
    setLoading(false);
  };

  const handleFileUpload = async (uploadedFile) => {
    setFile(uploadedFile);
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', uploadedFile);

    try {
      const response = await axios.post(`${API_BASE}/parse`, formData);
      setData(response.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to parse file. Make sure it is a valid .STD file.');
      setLoading(false);
    }
  };

  const downloadExcel = async () => {
    if (!file) return;
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API_BASE}/download`, formData, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${data?.filename || 'STAAD'}_Procurement.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Download failed', err);
      alert('Failed to download Excel file.');
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] text-slate-200 selection:bg-indigo-500/30">
      {/* Dynamic Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-5%] w-[50%] h-[50%] bg-indigo-600/10 rounded-full blur-[120px] animate-mesh" />
        <div className="absolute bottom-[-10%] right-[-5%] w-[50%] h-[50%] bg-violet-600/10 rounded-full blur-[120px] animate-mesh" style={{ animationDelay: '-5s' }} />
      </div>

      <Navbar onReset={resetApp} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 relative z-10">
        <AnimatePresence mode="wait">
          {!data && !loading ? (
            <motion.div
              key="upload-view"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex flex-col items-center justify-center min-h-[70vh]"
            >
              <div className="text-center mb-10 max-w-3xl">
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-bold uppercase tracking-widest mb-6"
                >
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                  </span>
                  v1.0.0 Now Live
                </motion.div>
                <motion.h1 
                  initial={{ opacity: 0, y: -20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="text-4xl sm:text-6xl font-extrabold bg-clip-text text-transparent bg-gradient-to-b from-white to-slate-400 mb-6 tracking-tight"
                >
                  Engineered for <span className="text-indigo-500">Procurement.</span>
                </motion.h1>
                <motion.p 
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 }}
                  className="text-slate-400 text-base sm:text-lg leading-relaxed px-4"
                >
                  The most advanced STAAD.Pro parser for material reporting. 
                  Upload your .STD file to generate weight breakdowns in seconds.
                </motion.p>
              </div>

              <FileUpload onUpload={handleFileUpload} error={error} />
            </motion.div>
          ) : loading ? (
            <motion.div
              key="loading-view"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center min-h-[60vh]"
            >
              <div className="relative w-28 h-28">
                <motion.div 
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                  className="absolute inset-0 border-b-2 border-indigo-500 rounded-full shadow-[0_0_15px_rgba(99,102,241,0.5)]"
                />
                <div className="absolute inset-4 border-t-2 border-slate-700 rounded-full animate-reverse-spin" />
                <FileUp className="absolute inset-0 m-auto w-10 h-10 text-indigo-400" />
              </div>
              <h2 className="mt-10 text-2xl font-bold text-white tracking-tight">Processing Matrix...</h2>
              <p className="text-slate-500 mt-2 text-sm">Extracting geometry & material data</p>
            </motion.div>
          ) : (
            <motion.div
              key="results-view"
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-8"
            >
              {/* Results Header */}
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-white/5">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-indigo-400 uppercase tracking-widest">
                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
                    Analysis Successful
                  </div>
                  <h2 className="text-2xl sm:text-4xl font-bold text-white tracking-tight break-all">
                    {data.filename}
                  </h2>
                </div>
                
                <div className="flex flex-wrap items-center gap-3">
                  <button 
                    onClick={resetApp}
                    className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-6 py-3 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all text-sm font-semibold"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Reset
                  </button>
                  <button 
                    onClick={downloadExcel}
                    className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-8 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 transition-all text-sm font-bold shadow-2xl shadow-indigo-600/30 group"
                  >
                    <Download className="w-4 h-4 transition-transform group-hover:translate-y-0.5" />
                    Get Report
                  </button>
                </div>
              </div>

              {/* Stats Grid */}
              <StatsGrid stats={data.stats} />

              {/* View Switcher - Scrollable on mobile */}
              <div className="overflow-x-auto pb-2 -mx-4 px-4 sm:mx-0 sm:px-0 scrollbar-none">
                <div className="flex items-center p-1.5 bg-slate-900/50 rounded-2xl border border-white/5 w-max sm:w-fit backdrop-blur-md">
                  {[
                    { id: 'summary', icon: BarChart3, label: 'Summary' },
                    { id: 'detail', icon: TableIcon, label: 'Members' },
                    { id: 'parts', icon: Layers, label: 'Parts' }
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setView(tab.id)}
                      className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 ${
                        view === tab.id 
                          ? 'bg-indigo-600 text-white shadow-xl shadow-indigo-600/20 scale-[1.02]' 
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <tab.icon className="w-4 h-4" />
                      {tab.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Main Data Content */}
              <motion.div 
                layout
                className="glass rounded-3xl overflow-hidden border border-white/5 shadow-3xl bg-slate-950/40"
              >
                <ResultsTable 
                  type={view} 
                  summary={data.summary} 
                  records={data.records} 
                  parts={data.part_breakup}
                />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
      
      {/* Footer Branding */}
      <footer className="max-w-7xl mx-auto px-6 py-12 text-center border-t border-white/5 opacity-50">
        <p className="text-xs font-medium tracking-[0.2em] uppercase text-slate-500">
          Precision Material Intelligence &copy; 2026
        </p>
      </footer>
    </div>
  );
}

export default App;
