import { useState } from 'react';
import ReconciliationCard from './components/ReconciliationCard';
import DataQualityPanel from './components/DataQualityPanel';

function App() {
  const [apiKey, setApiKey] = useState(() => {
    return typeof window !== 'undefined' ? localStorage.getItem('apiKey') || '' : '';
  });

  const handleApiKeyChange = (e) => {
    const key = e.target.value;
    setApiKey(key);
    if (typeof window !== 'undefined') {
      if (key) localStorage.setItem('apiKey', key);
      else localStorage.removeItem('apiKey');
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <header className="border-b border-slate-700 bg-slate-800/80 px-4 py-6">
        <div className="mx-auto max-w-4xl">
          <h1 className="text-2xl font-bold text-white">
            Clinical Data Reconciliation Engine
          </h1>
          <p className="mt-1 text-slate-400">
            EHR integration for medication reconciliation and data quality validation
          </p>
          <div className="mt-4">
            <label className="mb-1 block text-sm text-slate-400">API Key (x-api-key)</label>
            <input
              type="password"
              value={apiKey}
              onChange={handleApiKeyChange}
              placeholder="Enter your API key"
              className="w-full max-w-md rounded border border-slate-600 bg-slate-900 px-3 py-2 text-white placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl space-y-8 p-6">
        <ReconciliationCard apiKey={apiKey} />
        <DataQualityPanel apiKey={apiKey} />
      </main>
    </div>
  );
}

export default App;
