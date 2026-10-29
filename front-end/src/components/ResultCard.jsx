import { motion } from "framer-motion";

const GAUGE_MAX_RATIO = 3; // The gauge spans 0x to 3x the alert threshold

const formatNumber = (value) => value.toExponential(2);

function getOutcome(result) {
  const truthIsAttack = result.kind === "attack";
  if (result.correct) {
    return truthIsAttack ? "True positive: attack caught" : "True negative: benign traffic accepted";
  }
  return truthIsAttack ? "False negative: attack missed" : "False positive: false alarm";
}

export default function ResultCard({ result }) {
  if (!result) return null;

  const fillPercent = Math.min(result.score_ratio / GAUGE_MAX_RATIO, 1) * 100;
  const thresholdPercent = (1 / GAUGE_MAX_RATIO) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`p-5 sm:p-6 rounded-xl border ${
        result.is_attack
          ? "bg-rose-950/30 border-rose-800 text-rose-300"
          : "bg-emerald-950/30 border-emerald-800 text-emerald-300"
      }`}
    >
      <h2 className="text-lg sm:text-xl font-bold mb-1">
        {result.is_attack ? "Attack detected 🚨" : "Normal traffic ✅"}
      </h2>
      <p className="text-sm mb-4">
        Ground truth: <span className="font-mono font-semibold">{result.true_label}</span>
        {" · "}
        <span className={result.correct ? "text-emerald-400" : "text-amber-400"}>{getOutcome(result)}</span>
      </p>

      {/* Gauge: error relative to the threshold */}
      <div className="mb-4">
        <div className="relative h-3 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full ${result.is_attack ? "bg-rose-500" : "bg-emerald-500"}`}
            style={{ width: `${fillPercent}%` }}
          />
          <div
            className="absolute top-0 h-full w-0.5 bg-slate-100"
            style={{ left: `${thresholdPercent}%` }}
            title="Alert threshold"
          />
        </div>
        <p className="text-xs text-slate-400 mt-1">
          {result.score_ratio.toFixed(2)}× the alert threshold (white marker)
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 text-sm">
        <div className="bg-slate-950/50 p-3 sm:p-4 rounded-lg border border-slate-800 flex flex-col">
          <span className="text-slate-400 mb-1">Reconstruction error</span>
          <span className="font-mono font-bold text-base sm:text-lg text-slate-100 break-all">
            {formatNumber(result.reconstruction_error)}
          </span>
        </div>
        <div className="bg-slate-950/50 p-3 sm:p-4 rounded-lg border border-slate-800 flex flex-col">
          <span className="text-slate-400 mb-1">Alert threshold</span>
          <span className="font-mono font-bold text-base sm:text-lg text-slate-100 break-all">
            {formatNumber(result.threshold)}
          </span>
        </div>
      </div>
    </motion.div>
  );
}