export default function ActionButtons({ onTest, loading }) {
  return (
    <div className="flex gap-4 mb-8">
      <button
        onClick={() => onTest(false)}
        disabled={loading}
        className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg shadow-emerald-900/20 cursor-pointer disabled:opacity-50"
      >
        {loading ? "Analyse..." : "Tester Trafic Normal (BENIGN)"}
      </button>
      
      <button
        onClick={() => onTest(true)}
        disabled={loading}
        className="flex-1 bg-rose-600 hover:bg-rose-500 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg shadow-rose-900/20 cursor-pointer disabled:opacity-50"
      >
        {loading ? "Analyse..." : "Simuler une Attaque 🚨"}
      </button>
    </div>
  );
}