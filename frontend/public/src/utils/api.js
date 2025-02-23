// frontend/src/utils/api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export const captureScreen = async () => {
  const response = await fetch(`${API_BASE_URL}/scan`);
  if (!response.ok) {
    throw new Error('Failed to capture screen');
  }
  return response.json();
};
