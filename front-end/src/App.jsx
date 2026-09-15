import { useState } from 'react';
import axios from 'axios';
import Header from './components/Header';
import ActionButtons from './components/ActionButtons';
import ResultCard from './components/ResultCard';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleTestTraffic = async (isAttack) => {
    setLoading(true);

    // 🟢 BENIGN: Random small values to simulate normal fluctuating traffic
    const benignTraffic = new Array(78).fill(0).map(() => {
      // Generates a random number between 0.01 and 0.08
      return (Math.random() * 0.07) + 0.01; 
    });

    // 🚨 ATTACK: Normal background noise + random massive spikes
    const attackTraffic = new Array(78).fill(0).map((_, i) => {
      // Create random large spikes for specific features to trigger the anomaly
      if (i === 12 || i === 34 || i === 56 || i % 7 === 0) {
        // Generates a random high spike between 2.5 and 5.5
        return (Math.random() * 3) + 2.5; 
      }
      // General background noise for attack (between 0.1 and 0.3)
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
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-4 sm:p-6">
      <div className="max-w-2xl w-full bg-slate-900 border border-slate-800 rounded-2xl p-5 sm:p-8 shadow-2xl">
        <Header />
        <ActionButtons onTest={handleTestTraffic} loading={loading} />
        <ResultCard result={result} />
      </div>
    </div>
  );
}