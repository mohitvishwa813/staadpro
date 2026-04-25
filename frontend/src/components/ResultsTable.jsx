import React, { useState } from 'react';
import { Search, Filter } from 'lucide-react';

const ResultsTable = ({ type, summary, records, parts }) => {
  const [search, setSearch] = useState('');

  const filteredRecords = (records || []).filter(r => 
    r.member_id.toString().includes(search) || 
    r.part.toLowerCase().includes(search.toLowerCase())
  );

  const Th = ({ children, align = 'left' }) => (
    <th className={`px-6 py-5 text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 ${align === 'right' ? 'text-right' : ''}`}>
      {children}
    </th>
  );

  if (type === 'summary') {
    return (
      <div className="overflow-x-auto scrollbar-thin">
        <table className="w-full text-left border-collapse min-w-[700px]">
          <thead>
            <tr className="bg-white/[0.01] border-b border-white/5">
              <Th>Thickness</Th>
              <Th>Pieces</Th>
              <Th>Members</Th>
              <Th>Area (m²)</Th>
              <Th align="right">Weight (kg)</Th>
              <Th align="right">Weight (Ton)</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {summary.map((row, idx) => (
              <tr key={row.thickness_mm} className="hover:bg-indigo-500/[0.03] transition-colors group">
                <td className="px-6 py-5">
                  <span className="px-3 py-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 font-black text-sm border border-indigo-500/10 group-hover:bg-indigo-600 group-hover:text-white transition-all">
                    {row.thickness_mm} mm
                  </span>
                </td>
                <td className="px-6 py-5 text-slate-300 font-bold">{row.plate_count}</td>
                <td className="px-6 py-5 text-slate-400 font-medium">{row.member_count}</td>
                <td className="px-6 py-5 text-slate-400 font-mono text-sm">{row.total_area_m2.toFixed(3)}</td>
                <td className="px-6 py-5 text-right text-white font-black font-mono tracking-tighter">{row.total_weight_kg.toLocaleString()}</td>
                <td className="px-6 py-5 text-right text-indigo-400 font-black font-mono">{(row.total_weight_ton).toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (type === 'parts') {
    return (
      <div className="overflow-x-auto scrollbar-thin">
        <table className="w-full text-left border-collapse min-w-[700px]">
          <thead>
            <tr className="bg-white/[0.01] border-b border-white/5">
              <Th>Part Type</Th>
              <Th>Thickness</Th>
              <Th>Count</Th>
              <Th>Area (m²)</Th>
              <Th align="right">Weight (kg)</Th>
              <Th align="right">Weight (Ton)</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {parts.map((row, idx) => (
              <tr key={idx} className="hover:bg-indigo-500/[0.03] transition-colors group">
                <td className="px-6 py-5">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.6)]" />
                    <span className="font-black text-white uppercase text-xs tracking-widest">{row.part}</span>
                  </div>
                </td>
                <td className="px-6 py-5 text-slate-300 font-black text-sm">{row.thickness_mm} mm</td>
                <td className="px-6 py-5 text-slate-400 font-bold">{row.count}</td>
                <td className="px-6 py-5 text-slate-400 font-mono text-sm">{row.total_area_m2.toFixed(3)}</td>
                <td className="px-6 py-5 text-right text-white font-black font-mono">{row.total_weight_kg.toLocaleString()}</td>
                <td className="px-6 py-5 text-right text-indigo-400 font-black font-mono">{(row.total_weight_kg/1000).toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div>
      <div className="p-5 border-b border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/30">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input 
            type="text"
            placeholder="Search Member or Part..."
            className="w-full bg-slate-950/50 border border-white/5 rounded-2xl py-3 pl-12 pr-4 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all placeholder:text-slate-600"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-3 text-[10px] text-slate-500 font-black uppercase tracking-widest">
          <Filter className="w-3 h-3" />
          {filteredRecords.length} Records Found
        </div>
      </div>
      <div className="overflow-x-auto max-h-[600px] scrollbar-thin">
        <table className="w-full text-left border-collapse min-w-[800px]">
          <thead className="sticky top-0 z-20 bg-slate-950 shadow-sm">
            <tr className="border-b border-white/5">
              <Th>Member ID</Th>
              <Th>Part</Th>
              <Th>Thickness</Th>
              <Th>Length (m)</Th>
              <Th>Width (m)</Th>
              <Th align="right">Weight (kg)</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {filteredRecords.map((row, idx) => (
              <tr key={idx} className="hover:bg-indigo-500/[0.03] transition-colors group">
                <td className="px-6 py-5 font-black text-indigo-400 text-sm tracking-tight group-hover:text-white transition-colors">
                  #{row.member_id}
                </td>
                <td className="px-6 py-5">
                  <span className={`text-[10px] px-2.5 py-1 rounded-md font-black uppercase tracking-widest
                    ${row.part.includes('Web') ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/10' : 'bg-slate-800 text-slate-400 border border-white/5'}
                  `}>
                    {row.part}
                  </span>
                </td>
                <td className="px-6 py-5 text-slate-300 font-bold">{row.thickness_mm} mm</td>
                <td className="px-6 py-5 text-slate-400 font-mono text-sm">{row.length_m.toFixed(3)}</td>
                <td className="px-6 py-5 text-slate-400 font-mono text-sm">{row.width_m.toFixed(3)}</td>
                <td className="px-6 py-5 text-right text-white font-black font-mono tracking-tighter">{row.weight_kg.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ResultsTable;
