import { useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import Header from './components/Header';
import ActionButtons from './components/ActionButtons';
import ResultCard from './components/ResultCard';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [isWakingUp, setIsWakingUp] = useState(false); // Nouvel état pour le serveur endormi
  const [result, setResult] = useState(null);

  const handleTestTraffic = async (isAttack) => {
    setLoading(true);
    setIsWakingUp(false);
    setResult(null); // Cacher le résultat précédent pendant la nouvelle analyse

    // ⏱️ TIMER INTELLIGENT : Si après 4 secondes on n'a pas de réponse, 
    // on avertit l'utilisateur que le backend (Render) est en train de se réveiller.
    const wakeUpTimer = setTimeout(() => {
      setIsWakingUp(true);
    }, 4000);

    // 🟢 BENIGN: Random small values
    const benignTraffic = new Array(78).fill(0).map(() => {
      return (Math.random() * 0.07) + 0.01; 
    });

    // 🚨 ATTACK: Normal background noise + random massive spikes
    const attackTraffic = new Array(78).fill(0).map((_, i) => {
      if (i === 12 || i === 34 || i === 56 || i % 7 === 0) {
        return (Math.random() * 3) + 2.5; 
      }
      return (Math.random() * 0.2) + 0.1;
    });

    const payloadFeatures = isAttack ? attackTraffic : benignTraffic;

    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
      
      const response = await axios.post(`${apiUrl}/predict`, {
        features: payloadFeatures
      });
      setResult(response.data);
    } catch (err) {
      console.error(err);
      alert("Erreur de connexion au backend ! Vérifiez que FastAPI est lancé.");
    } finally {
      // 🛑 Quoi qu'il arrive, on arrête le chargement et on nettoie le timer
      clearTimeout(wakeUpTimer);
      setLoading(false);
      setIsWakingUp(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-4 sm:p-6">
      <div className="max-w-2xl w-full bg-slate-900 border border-slate-800 rounded-2xl p-5 sm:p-8 shadow-2xl relative overflow-hidden">
        
        {/* Décoration d'arrière-plan */}
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 via-indigo-500 to-purple-500"></div>

        <Header />
        
        <ActionButtons onTest={handleTestTraffic} loading={loading} />
        
        {/* === SECTION DE CHARGEMENT AMÉLIORÉE === */}
        {/* === NOUVELLE SECTION DE CHARGEMENT (SCANNER HORIZONTAL) === */}
        {loading && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center py-8"
          >
            {/* Nouvelle animation : Barre de scan réseau */}
            <div className="w-48 h-1.5 bg-slate-800 rounded-full mb-6 overflow-hidden relative shadow-inner">
              <motion.div
                animate={{ x: ["-100%", "200%"] }}
                transition={{ repeat: Infinity, duration: 1.2, ease: "easeInOut" }}
                className="w-1/2 h-full bg-gradient-to-r from-transparent via-indigo-500 to-transparent absolute top-0 left-0"
              />
            </div>

            {/* Texte dynamique */}
            <h3 className="text-lg font-semibold text-slate-200 mb-2">
              {isWakingUp ? "Réveil du serveur AI..." : "Analyse des paquets..."}
            </h3>
            
            <p className="text-sm text-slate-400 text-center max-w-sm">
              {isWakingUp 
                ? "Le backend gratuit sort de veille. Cela prend environ 50 secondes. Merci de patienter !" 
                : "Inspection des 78 features du trafic via l'Autoencoder."}
            </p>
          </motion.div>
        )}

        {/* N'affiche le résultat que s'il n'est pas en train de charger */}
        {!loading && <ResultCard result={result} />}
        
      </div>
    </div>
  );
}