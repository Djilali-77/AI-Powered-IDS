import { motion } from "framer-motion";

export default function Header() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="text-center mb-6 sm:mb-8"
    >
      <h1 className="text-2xl sm:text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-indigo-500 mb-2 sm:mb-3 leading-tight">
        AI-Powered Intrusion Detection System
      </h1>
      <p className="text-sm sm:text-base text-slate-400 px-2 sm:px-0">
        Unsupervised network anomaly detection with a PyTorch autoencoder, tested on real CICIDS2017 traffic.
      </p>
    </motion.div>
  );
}