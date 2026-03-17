import { useState } from 'react';
import { reconcileMedication } from '../api/client';
import ConfidenceGauge from './ConfidenceGauge';

const DEFAULT_SOURCES = [
  { system: 'ehr', medication: '', last_updated: new Date().toISOString().slice(0, 19), source_reliability: 'high' },
];

/**
 * Reconciliation UI: input form, reconciled output, confidence badge,
 * expandable reasoning, Approve/Reject (assignment requirement).
 */
export default function ReconciliationCard({ apiKey }) {
  const [patientAge, setPatientAge] = useState('');
  const [conditions, setConditions] = useState('');
  const [sources, setSources] = useState(DEFAULT_SOURCES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [decision, setDecision] = useState(null); // 'approved' | 'rejected'

  const addSource = () => {
    setSources([
      ...sources,
      { system: 'ehr', medication: '', last_updated: new Date().toISOString().slice(0, 19), source_reliability: 'medium' },
    ]);
  };

  const updateSource = (i, field, value) => {
    const next = [...sources];
    next[i] = { ...next[i], [field]: value };
    setSources(next);
  };

  const removeSource = (i) => {
    if (sources.length > 1) setSources(sources.filter((_, j) => j !== i));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setDecision(null);
    if (!apiKey) {
      setError('API key is required');
      return;
    }
    const validSources = sources.filter((s) => s.medication.trim());
    if (validSources.length === 0) {
      setError('At least one medication source is required');
      return;
    }
    setLoading(true);
    try {
      const payload = {
        patient_context: {
          age: patientAge ? parseInt(patientAge, 10) : null,
          conditions: conditions ? conditions.split(',').map((c) => c.trim()).filter(Boolean) : [],
          recent_labs: null,
        },
        sources: validSources.map((s) => ({
          system: s.system,
          medication: s.medication.trim(),
          last_updated: s.last_updated,
          source_reliability: s.source_reliability,
          last_filled: s.last_filled || undefined,
        })),
      };
      const data = await reconcileMedication(payload, apiKey);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-lg border border-slate-600 bg-slate-800/50 p-5">
      <h2 className="mb-4 text-lg font-semibold text-white">Medication Reconciliation</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm text-slate-400">Patient age</label>
          <input
            type="number"
            value={patientAge}
            onChange={(e) => setPatientAge(e.target.value)}
            className="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-white placeholder-slate-500"
            placeholder="e.g. 65"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-slate-400">Conditions (comma-separated)</label>
          <input
            type="text"
            value={conditions}
            onChange={(e) => setConditions(e.target.value)}
            className="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-white placeholder-slate-500"
            placeholder="e.g. diabetes, CKD"
          />
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <label className="text-sm text-slate-400">Medication sources</label>
            <button
              type="button"
              onClick={addSource}
              className="text-sm text-sky-400 hover:text-sky-300"
            >
              + Add source
            </button>
          </div>
          {sources.map((s, i) => (
            <div key={i} className="mb-3 flex flex-wrap gap-2 rounded border border-slate-600 bg-slate-900/50 p-3">
              <input
                type="text"
                value={s.medication}
                onChange={(e) => updateSource(i, 'medication', e.target.value)}
                className="flex-1 min-w-[120px] rounded border border-slate-600 bg-slate-800 px-2 py-1.5 text-sm text-white"
                placeholder="Medication"
              />
              <select
                value={s.system}
                onChange={(e) => updateSource(i, 'system', e.target.value)}
                className="rounded border border-slate-600 bg-slate-800 px-2 py-1.5 text-sm text-white"
              >
                <option value="ehr">EHR</option>
                <option value="pharmacy">Pharmacy</option>
                <option value="patient">Patient</option>
              </select>
              <select
                value={s.source_reliability}
                onChange={(e) => updateSource(i, 'source_reliability', e.target.value)}
                className="rounded border border-slate-600 bg-slate-800 px-2 py-1.5 text-sm text-white"
              >
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <input
                type="datetime-local"
                value={s.last_updated?.slice(0, 16) || ''}
                onChange={(e) => updateSource(i, 'last_updated', e.target.value ? `${e.target.value}:00` : '')}
                className="rounded border border-slate-600 bg-slate-800 px-2 py-1.5 text-sm text-white"
              />
              {sources.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeSource(i)}
                  className="text-red-400 hover:text-red-300"
                >
                  Remove
                </button>
              )}
            </div>
          ))}
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="rounded bg-sky-600 px-4 py-2 text-white hover:bg-sky-500 disabled:opacity-50"
        >
          {loading ? 'Reconciling…' : 'Reconcile'}
        </button>
      </form>

      {result && (
        <div className="mt-6 space-y-4 border-t border-slate-600 pt-6">
          <h3 className="text-sm font-medium text-slate-300">Result</h3>
          <p className="text-lg font-medium text-white">{result.reconciled_medication}</p>

          <ConfidenceGauge score={result.confidence_score} reasoning={result.reasoning} />

          {result.recommended_actions?.length > 0 && (
            <div>
              <h4 className="mb-1 text-sm text-slate-400">Recommended actions</h4>
              <ul className="list-inside list-disc text-sm text-slate-300">
                {result.recommended_actions.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          )}
          {result.clinical_safety_check && (
            <div className="rounded border border-slate-600 bg-slate-900/50 p-3 text-sm text-slate-300">
              <strong className="text-slate-400">Safety check:</strong> {result.clinical_safety_check}
            </div>
          )}

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setDecision('approved')}
              className={`rounded px-4 py-2 text-sm font-medium ${
                decision === 'approved'
                  ? 'bg-green-600 text-white'
                  : 'border border-green-600 text-green-400 hover:bg-green-600/20'
              }`}
            >
              Approve
            </button>
            <button
              type="button"
              onClick={() => setDecision('rejected')}
              className={`rounded px-4 py-2 text-sm font-medium ${
                decision === 'rejected'
                  ? 'bg-red-600 text-white'
                  : 'border border-red-600 text-red-400 hover:bg-red-600/20'
              }`}
            >
              Reject
            </button>
          </div>
          {decision && (
            <p className="text-sm text-slate-400">
              You {decision} this reconciliation.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
