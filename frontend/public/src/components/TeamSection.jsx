// frontend/src/components/TeamSection.jsx
import React from 'react';
import PlayerCard from './PlayerCard';

const TeamSection = ({ title, players, onLookup, className }) => {
  return (
    <div className={className}>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <div className="space-y-2">
        {players.map((player, idx) => (
          <PlayerCard 
            key={`${title}-${idx}`}
            player={player}
            onLookup={onLookup}
          />
        ))}
      </div>
    </div>
  );
};