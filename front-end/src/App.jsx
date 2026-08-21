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
    const mockFeatures = Array.from({ length: 78 }, () => 
      isAttack ? Math.random() * 5 - 2 : Math.random() * 0.1
    );

    try {
      const response = await axios.post("http://127.0.0.1:8000/predict", {
        features: mockFeatures
      });
      setResult(response.data);
    } catch (err) {
      console.error(err);
      alert("Erreur de connexion au backend !");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6">
      <div className="max-w-2xl w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        <Header />
        <ActionButtons onTest={handleTestTraffic} loading={loading} />
        <ResultCard result={result} />
      </div>
    </div>
  );
}