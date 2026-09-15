import { motion } from 'framer-motion';

export default function ResultCard({ result }) {
  if (!result) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`p-5 sm:p-6 rounded-xl border ${
        result.danger 
          ? 'bg-rose-950/30 border-rose-800 text-rose-300' 
          : 'bg-emerald-950/30 border-emerald-800 text-emerald-300'
      }`}
    >
      <h2 className="text-lg sm:text-xl font-bold mb-3">
        Résultat : {result.status}
      </h2>
      
      {/* grid-cols-1 on phones, grid-cols-2 on bigger screens */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 text-sm">
        <div className="bg-slate-950/50 p-3 sm:p-4 rounded-lg border border-slate-800 flex flex-col">
          <span className="text-slate-400 mb-1">Reconstruction Error:</span>
          {/* break-all prevents the long decimals from overflowing the box */}
          <span className="font-mono font-bold text-base sm:text-lg text-slate-100 break-all">
            {result.reconstruction_error.toFixed(6)}
          </span>
        </div>
        <div className="bg-slate-950/50 p-3 sm:p-4 rounded-lg border border-slate-800 flex flex-col">
          <span className="text-slate-400 mb-1">Threshold (Seuil):</span>
          {/* break-all applied here as well just in case */}
          <span className="font-mono font-bold text-base sm:text-lg text-slate-100 break-all">
            {result.threshold}
          </span>
        </div>
      </div>
    </motion.div>
  );
}