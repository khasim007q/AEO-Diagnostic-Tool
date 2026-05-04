# 🔍 AEO Diagnostic Tool

**AI Engine Optimization Diagnostic** — See how your product ranks across GPT-5-mini, Claude 4 Sonnet, and Gemini 2.5 Flash, cross-validated against real Google Search results.

## What It Does

1. Queries **GPT-5-mini**, **Claude 4 Sonnet**, and **Gemini 2.5 Flash** simultaneously via OpenRouter
2. Extracts **brand mentions** and ranking positions from each AI response
3. Cross-validates brands against **real Google Search results** via SerpApi
4. Generates a **visual report card** with scores, grades, gap analysis, and actionable insights

## Quick Start (Local)

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/aeo-diagnostic.git
cd aeo-diagnostic
pip install -r requirements.txt
```

### 2. Set Up API Keys

Edit the `.env` file with your real keys:

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxx
SERPAPI_KEY=xxxxx
```

- **OpenRouter**: Sign up at [openrouter.ai](https://openrouter.ai) → API Keys
- **SerpApi**: Sign up at [serpapi.com](https://serpapi.com) → Dashboard → API Key

### 3. Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Deploy to Streamlit Community Cloud

1. Commit and push your code to a GitHub repository.
2. Log in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **New app** and select your GitHub repository, branch, and `app.py` as the main file path.
4. Before clicking Deploy, go to **Advanced settings...** and paste your `.env` contents into the **Secrets** field:
   ```toml
   OPENROUTER_API_KEY="your-openrouter-key"
   SERPAPI_KEY="your-serpapi-key"
   ```
5. Click **Deploy!**

## Project Structure

```
aeo-diagnostic/
├── app.py              # Main Streamlit app (UI + orchestration)
├── llm_engine.py       # OpenRouter API calls (3 LLMs in parallel)
├── serp_engine.py      # SerpApi Google Search integration
├── parser.py           # Brand extraction from LLM responses
├── scorer.py           # Scoring, grading, insights, cross-validation
├── requirements.txt    # Python dependencies
├── .env                # API keys (gitignored)
├── .gitignore
└── README.md
```

## Tech Stack

| Layer | Tool |
|---|---|
| Frontend + App | Streamlit |
| LLM Queries | OpenRouter API (GPT-5-mini + Claude + Gemini) |
| Search Validation | SerpApi |
| Parsing | Python (regex + simple NLP) |
| Deployment | Streamlit Community Cloud |
| Language | Python 3.10+ |

## License

MIT
