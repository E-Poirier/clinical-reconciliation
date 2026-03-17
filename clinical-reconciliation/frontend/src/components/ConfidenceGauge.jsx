import { useState } from 'react';
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts';

/**
 * Visualize confidence score (0–1) with red/yellow/green indicator.
 * Expandable reasoning section per assignment requirement.
 */
export default function ConfidenceGauge({ score, reasoning }) {
  const [expanded, setExpanded] = useState(false);
  const percent = Math.round((score ?? 0) * 100);

  // Red < 0.5, Yellow 0.5–0.75, Green > 0.75
  const getColor = () => {
    if (score < 0.5) return '#ef4444'; // red
    if (score < 0.75) return '#eab308'; // yellow
    return '#22c55e'; // green
  };

  const data = [{ name: 'confidence', value: percent, fill: getColor() }];

  return (
    <div className="rounded-lg border border-slate-600 bg-slate-800/50 p-4">
      <h3 className="mb-3 text-sm font-medium text-slate-300">Confidence</h3>
      <div className="flex items-center gap-4">
        <div className="h-24 w-24 shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              innerRadius="70%"
              outerRadius="100%"
              data={data}
              startAngle={180}
              endAngle={0}
            >
              <RadialBar background dataKey="value" cornerRadius={4} />
            </RadialBarChart>
          </ResponsiveContainer>
        </div>
        <div className="flex-1">
          <div
            className="mb-1 inline-flex rounded-full px-2.5 py-0.5 text-sm font-medium"
            style={{
              backgroundColor: `${getColor()}33`,
              color: getColor(),
            }}
          >
            {percent}%
          </div>
          {reasoning && (
            <button
              type="button"
              onClick={() => setExpanded(!expanded)}
              className="text-left text-xs text-slate-400 hover:text-slate-300 underline"
            >
              {expanded ? 'Hide' : 'Show'} reasoning
            </button>
          )}
        </div>
      </div>
      {expanded && reasoning && (
        <div className="mt-3 rounded border border-slate-600 bg-slate-900/50 p-3 text-sm text-slate-300">
          {reasoning}
        </div>
      )}
    </div>
  );
}
