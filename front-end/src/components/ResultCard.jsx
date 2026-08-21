import { motion } from 'framer-motion';

export default function ResultCard({ result }) {
  if (!result) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`p-6 rounded-xl border ${
        result.danger 
          ? 'bg-rose-950/30 border-rose-800 text-rose-300' 
          : 'bg-emerald-950/30 border-emerald-800 text-emerald-300'
      }`}
    >
      <h2 className="text-xl font-bold mb-2">
        Résultat : {result.status}
      </h2>
      <div className="grid grid-cols-2 gap-4 text-sm mt-4">
        <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800">
          <span className="text-slate-400 block">Reconstruction Error:</span>
          <span className="font-mono font-bold text-lg text-slate-100">
            {result.reconstruction_error.toFixed(6)}
          </span>
        </div>
        <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800">
          <span className="text-slate-400 block">Threshold (Seuil):</span>
          <span className="font-mono font-bold text-lg text-slate-100">
            {result.threshold}
          </span>
        </div>
      </div>
    </motion.div>
  );
}