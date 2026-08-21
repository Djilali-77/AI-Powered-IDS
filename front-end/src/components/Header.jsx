import { motion } from 'framer-motion';

export default function Header() {
  return (
    <motion.div 
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="text-center mb-8"
    >
      <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-indigo-500 mb-2">
        AI-Powered Intrusion Detection System
      </h1>
      <p className="text-slate-400">
        Système de surveillance réseau intelligent basé sur un Autoencoder (Deep Learning).
      </p>
    </motion.div>
  );
}