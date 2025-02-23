// frontend/src/components/LoadingSpinner.jsx
import React from 'react';

const LoadingSpinner = () => (
  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-200" />
);

// frontend/src/hooks/useScreenCapture.js
import { useState } from 'react';
import { captureScreen } from '../utils/api';

export const useScreenCapture = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const capture = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await captureScreen();
      return data.players;
    } catch (err) {
      setError(err.message);
      return [];
    } finally {
      setLoading(false);
    }
  };

  return { capture, loading, error };
};