# Salesforce Lead Qualifier

Automated B2B lead qualification service integrating **Salesforce REST API**, **Python**, **Pydantic**, **Google Gemini Structured Outputs**, and **FastAPI**.

Designed for reliability, idempotency, and clean separation between deterministic scoring rules and LLM-based semantic enrichment.

## Architecture & Flow

- **Extract:** Query inbound leads from Salesforce via SOQL (OAuth2 Client Credentials).
- **Validate:** Parse and validate raw records with Pydantic (`LeadInput`).
- **Deterministic Score:** Evaluate corporate email domains, company presence, description depth, and high-intent keywords (0-100 mapped to `Hot`, `Warm`, or `Cold`).
- **AI Enrichment:** Use `google-genai` with strict Pydantic structured outputs (`AILeadInsights`) to evaluate domain-company alignment, extract pain points, classify urgency, and generate an executive summary (with safe fallback to deterministic scoring).
- **Idempotency & Sync:** Skip `PATCH` calls if the lead rating and summary are unchanged; otherwise update Salesforce.

## Project Structure

- `src/config.py` - Environment validation via `pydantic-settings`
- `src/salesforce_client.py` - OAuth2, SOQL query, and PATCH client with `tenacity` retries
- `src/qualifier.py` - Deterministic + Gemini structured qualification engine
- `src/main.py` - Idempotent batch runner
- `src/api.py` - FastAPI endpoints (`/health`, `/qualify-lead`)
- `tests/test_qualifier.py` - Offline unit tests (`pytest`)
- `Dockerfile` - Containerized deployment

## Quickstart

1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in your Salesforce and Gemini credentials.
3. Run offline tests: `pytest`
4. Run batch qualification: `python -m src.main`
5. Run API server: `uvicorn src.api:app --reload` (docs at `http://127.0.0.1:8000/docs`)

## Docker

- Build: `docker build -t salesforce-lead-qualifier .`
- Run API: `docker run --env-file .env -p 8000:8000 salesforce-lead-qualifier`
- Run Batch: `docker run --env-file .env salesforce-lead-qualifier python -m src.main`
