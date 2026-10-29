import { motion } from "framer-motion";

export default function LoadingScanner({ isWakingUp, inputDim }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-8"
    >
      {/* Horizontal network-scan bar */}
      <div className="w-48 h-1.5 bg-slate-800 rounded-full mb-6 overflow-hidden relative shadow-inner">
        <motion.div
          animate={{ x: ["-100%", "200%"] }}
          transition={{ repeat: Infinity, duration: 1.2, ease: "easeInOut" }}
          className="w-1/2 h-full bg-gradient-to-r from-transparent via-indigo-500 to-transparent absolute top-0 left-0"
        />
      </div>

      <h3 className="text-lg font-semibold text-slate-200 mb-2">
        {isWakingUp ? "Waking up the AI server..." : "Analyzing network flow..."}
      </h3>

      <p className="text-sm text-slate-400 text-center max-w-sm">
        {isWakingUp
          ? "The free-tier backend is coming out of sleep. This takes about 50 seconds, thanks for your patience!"
          : `Inspecting ${inputDim ?? "all"} flow features with the autoencoder.`}
      </p>
    </motion.div>
  );
}