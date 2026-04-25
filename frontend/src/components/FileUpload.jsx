import React, { useState } from 'react';
import { Upload, FileText, AlertCircle, X, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

const FileUpload = ({ onUpload, error }) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.toUpperCase().endsWith('.STD')) {
        setSelectedFile(file);
      } else {
        alert("Please upload a .STD file");
      }
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const clearFile = (e) => {
    e.stopPropagation();
    setSelectedFile(null);
  };

  const handleSubmit = () => {
    if (selectedFile) {
      onUpload(selectedFile);
    }
  };

  return (
    <div className="w-full max-w-2xl px-4">
      <div 
        className={`relative group rounded-[2.5rem] border-2 border-dashed transition-all duration-500 p-8 sm:p-12 text-center overflow-hidden
          ${dragActive ? 'border-indigo-500 bg-indigo-500/10 scale-[1.02]' : 'border-slate-800 hover:border-slate-600 bg-white/[0.02]'}
          ${selectedFile ? 'border-indigo-500/30 bg-indigo-500/5' : ''}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          className="hidden"
          onChange={handleChange}
          accept=".std,.STD"
        />
        
        <div className="flex flex-col items-center">
          {!selectedFile ? (
            <label 
              htmlFor="file-upload" 
              className="flex flex-col items-center cursor-pointer w-full h-full"
            >
              <div className="w-20 h-20 bg-indigo-600/10 rounded-[2rem] flex items-center justify-center mb-8 group-hover:bg-indigo-600/20 group-hover:scale-110 transition-all duration-500 shadow-inner">
                <Upload className="w-10 h-10 text-indigo-500" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-3 tracking-tight">Click or Drop file here</h3>
              <p className="text-slate-500 text-sm font-medium px-4">Select a STAAD.Pro (.STD) file to begin analysis</p>
            </label>
          ) : (
            <motion.div 
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="w-full"
            >
              <div className="flex items-center gap-4 sm:gap-6 bg-slate-900/60 p-5 rounded-[2rem] border border-white/5 mb-8 shadow-inner">
                <div className="w-16 h-16 bg-indigo-500/20 rounded-2xl flex items-center justify-center shrink-0">
                  <FileText className="w-8 h-8 text-indigo-400" />
                </div>
                <div className="flex-1 text-left overflow-hidden">
                  <p className="text-white font-bold truncate text-lg">{selectedFile.name}</p>
                  <p className="text-slate-500 text-sm font-semibold uppercase tracking-widest">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                </div>
                <button 
                  onClick={clearFile}
                  className="p-3 hover:bg-white/10 rounded-full transition-colors text-slate-400 hover:text-white"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
              <button
                onClick={handleSubmit}
                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-black py-5 rounded-3xl transition-all shadow-2xl shadow-indigo-600/40 active:scale-[0.97] flex items-center justify-center gap-3 text-lg group"
              >
                Run Analysis
                <ChevronRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
              </button>
            </motion.div>
          )}
        </div>
      </div>

      {error && (
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 p-5 rounded-3xl bg-red-500/10 border border-red-500/20 flex items-center gap-4 text-red-400 text-sm font-semibold shadow-lg"
        >
          <AlertCircle className="w-6 h-6 shrink-0" />
          {error}
        </motion.div>
      )}
    </div>
  );
};

export default FileUpload;
