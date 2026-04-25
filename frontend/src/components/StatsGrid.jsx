import React from 'react';
import { motion } from 'framer-motion';
import { Scale, Layers, Maximize, Weight } from 'lucide-react';

const StatsGrid = ({ stats }) => {
  const items = [
    { 
      label: 'Total Members', 
      value: stats.total_members, 
      unit: 'IDs', 
      icon: Layers, 
      color: 'indigo' 
    },
    { 
      label: 'Thicknesses', 
      value: stats.thicknesses_mm.length, 
      unit: 'Variants', 
      icon: Scale, 
      color: 'violet' 
    },
    { 
      label: 'Surface Area', 
      value: stats.total_area_m2, 
      unit: 'm²', 
      icon: Maximize, 
      color: 'cyan' 
    },
    { 
      label: 'Net Weight', 
      value: stats.total_weight_ton, 
      unit: 'Tons', 
      icon: Weight, 
      color: 'indigo' 
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
      {items.map((item, idx) => (
        <motion.div
          key={item.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: idx * 0.1 }}
          className="glass-card p-6 sm:p-8 rounded-[2rem] border border-white/5 relative group overflow-hidden"
        >
          {/* Subtle background glow */}
          <div className={`absolute -right-4 -top-4 w-24 h-24 bg-${item.color}-500/5 rounded-full blur-3xl transition-all group-hover:bg-${item.color}-500/10`} />
          
          <div className="flex items-center justify-between mb-6">
            <div className={`p-4 rounded-2xl bg-slate-900/80 border border-white/5 shadow-inner`}>
              <item.icon className={`w-6 h-6 text-indigo-400`} />
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-slate-500 text-xs font-black uppercase tracking-[0.2em]">{item.label}</p>
            <div className="flex items-baseline gap-2">
              <h3 className="text-3xl font-black text-white tracking-tight">
                {typeof item.value === 'number' ? item.value.toLocaleString() : item.value}
              </h3>
              <span className="text-slate-400 text-xs font-bold uppercase">{item.unit}</span>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
};

export default StatsGrid;
