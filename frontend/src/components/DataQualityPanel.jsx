import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts';
import { validateDataQuality } from '../api/client';

const DIMENSIONS = [
  { key: 'completeness', label: 'Completeness' },
  { key: 'accuracy', label: 'Accuracy' },
  { key: 'timeliness', label: 'Timeliness' },
  { key: 'clinical_plausibility', label: 'Clinical Plausibility' },
];

/**
 * Score color: red < 50, yellow 50–75, green > 75
 */
function scoreColor(score) {
  if (score < 50) return '#ef4444';
  if (score < 75) return '#eab308';
  return '#22c55e';
}

/**
 * Data quality UI: overall score with red/yellow/green, 4 dimension bars, issues list.
 */
export default function DataQualityPanel({ apiKey }) {
  const [demographics, setDemographics] = useState({ age: '' });
  const [vitalSigns, setVitalSigns] = useState({ systolic_bp: '', diastolic_bp: '', heart_rate: '' });
  const [allergies, setAllergies] = useState('');
  const [lastUpdated, setLastUpdated] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    if (!apiKey) {
      setError('API key is required');
      return;
    }
    setLoading(true);
    try {
      const payload = {
        demographics: demographics.age ? { age: parseInt(demographics.age, 10) } : null,
        vital_signs:
          vitalSigns.systolic_bp || vitalSigns.diastolic_bp || vitalSigns.heart_rate
            ? {
                ...(vitalSigns.systolic_bp && { systolic_bp: parseInt(vitalSigns.systolic_bp, 10) }),
                ...(vitalSigns.diastolic_bp && { diastolic_bp: parseInt(vitalSigns.diastolic_bp, 10) }),
                ...(vitalSigns.heart_rate && { heart_rate: parseInt(vitalSigns.heart_rate, 10) }),
              }
            : null,
        allergies: allergies ? allergies.split(',').map((a) => a.trim()).filter(Boolean) : [],
        last_updated: lastUpdated ? `${lastUpdated}T12:00:00` : null,
      };
      const data = await validateDataQuality(payload, apiKey);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  const chartData = result?.breakdown
    ? DIMENSIONS.map((d) => ({
        name: d.label,
        score: result.breakdown[d.key],
        fill: scoreColor(result.breakdown[d.key]),
      }))
    : [];

  const overallColor = result ? scoreColor(result.overall_score) : '#64748b';

  return (
    <div className="rounded-lg border border-slate-600 bg-slate-800/50 p-5">
      <h2 className="mb-4 text-lg font-semibold text-white">Data Quality Validation</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm text-slate-400">Age</label>
            <input
              type="number"
              value={demographics.age}
              onChange={(e) => setDemographics({ ...demographics, age: e.target.value })}
              className="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-white"
              placeholder="e.g. 65"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-400">Last updated (date)</label>
            <input
              type="date"
              value={lastUpdated}
              onChange={(e) => setLastUpdated(e.target.value)}
              className="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-white"
            />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-sm text-slate-400">Vital signs</label>
          <div className="flex flex-wrap gap-2">
            <input
              type="number"
              value={vitalSigns.systolic_bp}
              onChange={(e) => setVitalSigns({ ...vitalSigns, systolic_bp: e.target.value })}
              className="rounded border border-slate-600 bg-slate-900 px-3 py-2 text-white"
              placeholder="Systolic BP"
            />
            <input
              type="number"
              value={vitalSigns.diastolic_bp}
              onChange={(e) => setVitalSigns({ ...vitalSigns, diastolic_bp: e.target.value })}
              className="rounded border border-slate-600 bg-slate-900 px-3 py-2 text-white"
              placeholder="Diastolic BP"
            />
            <input
              type="number"
              value={vitalSigns.heart_rate}
              onChange={(e) => setVitalSigns({ ...vitalSigns, heart_rate: e.target.value })}
              className="rounded border border-slate-600 bg-slate-900 px-3 py-2 text-white"
              placeholder="Heart rate"
            />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-sm text-slate-400">Allergies (comma-separated, empty = none documented)</label>
          <input
            type="text"
            value={allergies}
            onChange={(e) => setAllergies(e.target.value)}
            className="w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-white"
            placeholder="e.g. Penicillin, Latex (leave empty to test 'no allergies' flag)"
          />
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="rounded bg-sky-600 px-4 py-2 text-white hover:bg-sky-500 disabled:opacity-50"
        >
          {loading ? 'Validating…' : 'Validate'}
        </button>
      </form>

      {result && (
        <div className="mt-6 space-y-4 border-t border-slate-600 pt-6">
          <h3 className="text-sm font-medium text-slate-300">Results</h3>

          <div className="flex items-center gap-4">
            <div
              className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full text-xl font-bold"
              style={{
                backgroundColor: `${overallColor}33`,
                color: overallColor,
              }}
            >
              {result.overall_score}
            </div>
            <div>
              <p className="text-sm text-slate-400">Overall score (0–100)</p>
              <p className="text-slate-300">
                <span
                  className="inline-block h-3 w-3 rounded-full mr-1"
                  style={{ backgroundColor: overallColor }}
                />
                {result.overall_score < 50 && 'Poor'}
                {result.overall_score >= 50 && result.overall_score < 75 && 'Fair'}
                {result.overall_score >= 75 && 'Good'}
              </p>
            </div>
          </div>

          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ left: 0, right: 20 }}>
                <XAxis type="number" domain={[0, 100]} tick={{ fill: '#94a3b8' }} />
                <YAxis type="category" dataKey="name" width={140} tick={{ fill: '#94a3b8' }} />
                <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                  {chartData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {result.issues_detected?.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-medium text-slate-400">Issues detected</h4>
              <ul className="space-y-2">
                {result.issues_detected.map((issue, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 rounded border border-slate-600 bg-slate-900/50 p-3"
                  >
                    <span
                      className="mt-0.5 h-2 w-2 shrink-0 rounded-full"
                      style={{
                        backgroundColor:
                          issue.severity === 'high'
                            ? '#ef4444'
                            : issue.severity === 'medium'
                            ? '#eab308'
                            : '#22c55e',
                      }}
                    />
                    <div>
                      <span className="text-sm font-medium text-slate-300">{issue.field}</span>
                      <span className="mx-1 text-slate-500">·</span>
                      <span className="text-sm text-slate-400">{issue.severity}</span>
                      <p className="mt-0.5 text-sm text-slate-300">{issue.issue}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
