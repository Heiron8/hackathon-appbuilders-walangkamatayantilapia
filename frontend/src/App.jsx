import { vocabulary } from './vocabulary.js';

// RobinKielll replaces this entry point after human Figma approval.
// Startup intentionally has no API/AI dependency.
export default function App() {
  return (
    <main>
      <h1>Tanaw</h1>
      <p>Application foundation ready: {vocabulary.version}, {vocabulary.cards.length} cards.</p>
      <p>Communication interface pending approved design integration.</p>
    </main>
  );
}
