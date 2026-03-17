/**
 * API client for Clinical Data Reconciliation Engine.
 * Proxies /api to backend (see vite.config.js).
 */

import axios from 'axios';

const API_BASE = '/api';

/**
 * Create axios instance with API key header.
 * @param {string} apiKey - API key for authentication (x-api-key)
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
