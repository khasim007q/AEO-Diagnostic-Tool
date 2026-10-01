# AEO Diagnostic Tool

A production-grade Answer Engine Optimization (AEO) diagnostic platform that measures brand visibility and recommendation prominence across frontier AI models (GPT-5-mini, Claude Sonnet 4, Gemini 2.5 Flash) and correlates them with independent organic Google search results.

---

## 1. System Architecture

The project consists of a decoupled, high-performance architecture:

* **Backend (`/backend`)**: FastAPI application providing async endpoints, strict JSON schema validation, parallel model execution via OpenRouter, resilient retry logic, and independent Google SERP corroboration.
* **Frontend (`/frontend`)**: React 18 + TypeScript + Vite application utilizing Tailwind CSS, Shadcn UI component design, TanStack Query for state management, Recharts for cross-engine benchmarks, and Zod for runtime network validation.
* **LLM Engine Integration**: OpenRouter API invoking GPT-5-mini, Claude Sonnet 4, and Gemini 2.5 Flash with strict structured JSON schema.
* **Search Corroboration**: SerpApi executing organic Google queries localized to targeted markets and domains.

---

## 2. Deterministic AI Visibility Scoring

The diagnostic replaces prototype scoring heuristics with a mathematical, bounded 0-100 AI Visibility Score:

### Position Score Weights (Top 5 Recommendations)
* Rank 1 = 1.00
* Rank 2 = 0.80
* Rank 3 = 0.60
* Rank 4 = 0.40
* Rank 5 = 0.20
* Not Mentioned / Absent = 0.00

### Brand Entity vs Product Evidence Separation
* In each engine run, each brand receives exactly **one** scoring observation.
* If an engine returns multiple products for the same brand (e.g. Nike Pegasus at #1 and Nike Vaporfly at #4), **only the best rank (#1, score 1.00)** contributes to the brand score.
* All returned products are preserved as supporting evidence in the brand details hierarchy.
* Scores for multiple products are never summed.

### Score Aggregation Across Engines
Across all successful engines ($S$):

$$\text{AI Visibility Score} = 100 \times \frac{\sum_{i=1}^S \text{position\_score}_i}{S}$$

* No consensus multipliers are applied.
* No Google search bonus is added to the AI score.
* The score is guaranteed to remain strictly between 0 and 100.
* If an engine fails (e.g., timeout, rate limit exhausted), it is excluded from the denominator $S$ so the brand score is not unfairly penalized, but the failure is reported in engine availability telemetry.

---

## 3. Explicit Supporting Metrics

The diagnostic reports explicit, uncoupled supporting metrics alongside the primary score:

* **ai_visibility_score**: Mean position score across successful engines (0 to 100).
* **engine_availability**: Ratio of successful engines to configured engines ($\frac{\text{successful}}{\text{configured}}$).
* **mention_coverage**: Ratio of engines mentioning the brand to successful engines ($\frac{\text{mentioned}}{\text{successful}}$).
* **median_rank**: Median rank observed across engines where the brand appeared.
* **average_rank**: Mean rank observed across engines where the brand appeared.
* **best_rank** / **worst_rank**: Extremes of brand placement across engines.
* **successful_engine_count** and **mentioned_engine_count**: Explicit integers making denominators transparent.

---

## 4. Entity Resolution Pipeline

Brand matching uses deterministic priority rules to prevent inaccurate mergers:

1. **Exact Normalized Match**: Lowercased, stripped of legal corporate suffixes (Inc, LLC, Corp, Ltd, etc.) and punctuation.
2. **Explicit Alias Match**: Canonical lookup table (e.g. "ON" resolves to "Optimum Nutrition", "MSFT" resolves to "Microsoft").
3. **Domain Match**: Candidate domain root matching known entity domain.
4. **Deterministic Containment**: Exact whole-word boundary matching.
5. **Strict Fuzzy Match**: Token sort ratio with a high confidence threshold ($\ge 88$).
6. **Ambiguity Rejection**: If the top two candidate matches are within 5 points of each other, the match is rejected rather than guessed.

---

## 5. Google Search Corroboration

Google Search is treated as an independent benchmark rather than an AI score component:

* The web authority bonus has been removed from AI visibility scores.
* Results are labeled **Search Corroboration** or **Google Presence**, avoiding claims like "AI validated".
* Each organic search snippet is evaluated independently across title match, snippet match, domain match, and confidence score.
* Distinct states are reported: `success`, `not_configured` (missing SERP API key), and `failed` (quota or network error).

---

## 6. Signed Gap Analysis

When a target brand is provided, head-to-head gaps against competitors are calculated:

$$\text{Signed Gap} = \text{Target Brand Score} - \text{Competitor Score}$$

* The sign is strictly preserved (no absolute value).
* A positive gap ($+20.0$) indicates the target brand leads.
* A negative gap ($-30.0$) indicates the competitor leads.
* A zero gap ($0.0$) indicates a tie.

---

## 7. Running the Application Locally

### Prerequisites
* Python 3.11+
* Node.js 18+ and npm

### Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your OPENROUTER_API_KEY and optional SERPAPI_KEY

uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Running Test Suites
```bash
# Backend tests (89 tests covering parser, scoring, fuzzy matching, segmentation, api)
pytest backend/tests/ -v

# Frontend tests (20 tests covering UI components, charts, and API validation)
cd frontend
npm test

# Frontend type checking and linting
npm run typecheck
npm run lint
npm run build
```

---

## 8. Deployment Configurations

* **Backend (Render)**: Configured via `render.yaml` with explicit CORS origins and health checks.
* **Frontend (Vercel)**: Configured via `vercel.json` with SPA route rewrites.

---

## 9. Diagnostic Disclaimer

These diagnostic results reflect a query-specific snapshot across selected AI models and search engines at execution time. They are not general brand endorsements or guarantees of future model responses.
