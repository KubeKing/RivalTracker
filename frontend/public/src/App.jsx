// frontend/src/App.jsx
import React, { useState } from 'react';
import { useScreenCapture } from './hooks/useScreenCapture';
import TeamSection from './components/TeamSection';
import LoadingSpinner from './components/LoadingSpinner';

const App = () => {
  const [players, setPlayers] = useState([]);
  const { capture, loading, error } = useScreenCapture();

  const handleCapture = async () => {
    const newPlayers = await capture();
    setPlayers(newPlayers);
  };

  const handleLookup = (playerName) => {
    window.open(
      `https://tracker.gg/marvel-rivals/profile/${encodeURIComponent(playerName)}`,
      '_blank'
    );
  };

  return (
    <div className="min-h-screen bg-slate-900 p-4">
      <div className="max-w-4xl mx-auto">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-white">Marvel Rivals Tracker</h1>
        </header>

        <div className="mb-6">
          <button
            onClick={handleCapture}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded flex items-center gap-2"
          >
            {loading ? <LoadingSpinner /> : 'Scan Game Screen'}
          </button>
          {error && (
            <p className="mt-2 text-red-400">{error}</p>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <TeamSection
            title="Your Team"
            players={players.slice(0, 6)}
            onLookup={handleLookup}
            className="text-blue-400"
          />
          <TeamSection
            title="Enemy Team"
            players={players.slice(6)}
            onLookup={handleLookup}
            className="text-red-400"
          />
        </div>
      </div>
    </div>
  );
};

export default App;