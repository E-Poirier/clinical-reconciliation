/**
 * HTTP helpers for the Clinical Data Reconciliation Engine.
 * In dev, Vite proxies `/api` to the backend (see vite.config.js).
 */

import axios from 'axios';

const API_BASE = '/api';

/**
 * @param {string} [apiKey] - Sent as `x-api-key` when present
 */
export function createClient(apiKey) {
  return axios.create({
    baseURL: API_BASE,
    headers: {
      'Content-Type': 'application/json',
      ...(apiKey && { 'x-api-key': apiKey }),
    },
  });
}

/**
 * Reconcile medication from multiple sources.
 * @param {object} payload - ReconcileRequest
 * @param {string} apiKey
 */
export async function reconcileMedication(payload, apiKey) {
  const client = createClient(apiKey);
  const { data } = await client.post('/reconcile/medication', payload);
  return data;
}

/**
 * Validate data quality.
 * @param {object} payload - DataQualityRequest
 * @param {string} apiKey
 */
export async function validateDataQuality(payload, apiKey) {
  const client = createClient(apiKey);
  const { data } = await client.post('/validate/data-quality', payload);
  return data;
}
