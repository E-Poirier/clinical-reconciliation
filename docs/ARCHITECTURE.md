# Architecture Decisions

Brief rationale for key technical choices in the Clinical Data Reconciliation Engine.

---

## 1. Hybrid Deterministic + LLM

**Decision:** Run rule-based checks first; use the LLM only for plausibility and reconciliation.

**Why:** Rules handle known cases (BP > 250, HR < 20, empty allergies) quickly and cheaply. The LLM is used where judgment is needed (e.g. “Is this value plausible for this patient?”). This reduces tokens, latency, and cost while keeping clinical safety.

---

## 2. In-Memory LLM Cache

**Decision:** Cache LLM responses by `hash(system_prompt + user_prompt)` in a Python dict.

**Why:** Avoids duplicate API calls for identical inputs (e.g. repeated validation). No Redis or external store keeps the setup simple. Trade-off: cache is lost on restart and not shared across processes.

---

## 3. Rule-First Data Quality

**Decision:** Clinical rules flag issues; the LLM only reviews flagged fields.

**Why:** Sending only flagged fields to the LLM cuts token usage. Rules cover most obvious problems; the LLM adds nuance for borderline cases.

---

## 4. JSON-Only LLM Output

**Decision:** Prompts require raw JSON; no markdown code fences. Parser strips fences if present.

**Why:** Reliable parsing. Fallback to deterministic results if parsing fails. Some models add markdown; the parser handles that.

---

## 5. API Key Authentication

**Decision:** Validate `x-api-key` header against `API_KEY` environment variable.

**Why:** Simple and sufficient for internal/demo use. No OAuth or JWT. Easy to rotate via env vars.

---

## 6. FastAPI + React + Vite

**Decision:** FastAPI backend, React frontend, Vite for dev/build.

**Why:** FastAPI gives async support and automatic OpenAPI docs. React + Vite provide a modern frontend with fast HMR. Vite proxy forwards `/api` to the backend in development.

---

## 7. Confidence Score Weights

**Decision:** Recency 35%, source reliability 25%, clinical alignment 25%, pharmacy 15%.

**Why:** Recency is weighted highest because medication lists change often. Source reliability reflects system trust. Clinical alignment and pharmacy data support adherence and safety.

---

## 8. Docker Compose for Integration

**Decision:** Docker Compose runs backend and frontend; frontend proxies `/api` to backend via `VITE_API_BACKEND`.

**Why:** Single command to run the full stack. Frontend uses the backend service name for API calls inside the Docker network.
