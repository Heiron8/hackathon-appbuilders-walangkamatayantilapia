import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import { verifiedSpeechProfile } from './speech-profile.mjs';

createRoot(document.getElementById('root')).render(<StrictMode><App speechConfiguration={verifiedSpeechProfile} /></StrictMode>);
