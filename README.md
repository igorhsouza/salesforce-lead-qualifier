<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=180&color=0:001F3F,50:0052A3,100:007ACC&text=Salesforce%20Lead%20Qualifier&fontColor=ffffff&fontSize=42&fontAlignY=38&desc=Hybrid%20B2B%20Lead%20Scoring%20%7C%20REST%20API%20and%20Gemini&descAlignY=62&descSize=16" alt="Salesforce Lead Qualifier" />
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&pause=1200&color=007ACC&center=true&vCenter=true&width=720&lines=Rules+first%2C+AI+where+it+adds+value;Deterministic+scoring+%2B+Gemini+structured+outputs;Idempotent+Salesforce+REST+API+sync;FastAPI+webhook+and+scheduled+batch+modes" alt="Typing animation" />
</p>

<p align="center">
  <a href="https://github.com/igorhsouza/salesforce-lead-qualifier/actions/workflows/ci.yml"><img src="https://github.com/igorhsouza/salesforce-lead-qualifier/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <img src="https://img.shields.io/badge/Python-3.12-007ACC?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Salesforce-00A1E0?style=flat-square&logo=salesforce&logoColor=white" alt="Salesforce" />
  <img src="https://img.shields.io/badge/Gemini-Structured%20Outputs-0052A3?style=flat-square&logo=googlegemini&logoColor=white" alt="Gemini" />
  <img src="https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic&logoColor=white" alt="Pydantic" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker" />
</p>

<table>
  <tr>
    <td width="50%" valign="top">
      <h3><img src="https://api.iconify.design/lucide/brain-circuit.svg?color=%23007ACC&width=22" alt="" /> Hybrid Intelligence</h3>
      Explicit deterministic rules handle baseline scoring (0-100), while Gemini enriches leads with pain points, urgency, and executive summaries - falling back safely if the LLM is unavailable.
    </td>
    <td width="50%" valign="top">
      <h3><img src="https://api.iconify.design/lucide/shield-check.svg?color=%23007ACC&width=22" alt="" /> Idempotent & Resilient</h3>
      Separates generated qualification summaries from original lead notes, skips redundant Salesforce <code>PATCH</code> calls, and retries transient failures with exponential backoff.
    </td>
  </tr>
</table>

<h2 align="center"><img src="https://api.iconify.design/lucide/workflow.svg?color=%23007ACC&width=26" alt="" /> Architecture & Flow</h2>

```text
Salesforce Lead (SOQL Query / Webhook Payload)
        |
        v
  Pydantic Validation (LeadInput)
        |
        v
  Deterministic Scoring Engine (0-100 -> Hot / Warm / Cold)
        |
        v
  Gemini Structured Enrichment (AILeadInsights + Safe Fallback)
        |
        v
  Idempotency Check ---> Skip if Rating & Summary unchanged
        | (if changed)
        v
  Salesforce REST PATCH (Updates Rating + Preserves Description)
```

<h2 align="center"><img src="https://api.iconify.design/lucide/play-circle.svg?color=%23007ACC&width=26" alt="" /> Quick Demo (Input -> Output)</h2>

**Request (`POST /qualify-lead`):**

```json
{
  "id": "00QgK00000ZwndhUAB",
  "name": "Ana Silva",
  "company": "Acme Automacoes",
  "email": "ana@acmeautomacoes.com.br",
  "description": "We need urgent API integration and workflow automation for our sales team.",
  "use_ai": true,
  "sync_to_salesforce": true
}
```

**Response (`200 OK`):**

```json
{
  "qualification": {
    "lead_id": "00QgK00000ZwndhUAB",
    "score": 100,
    "rating": "Hot",
    "is_corporate_email": true,
    "reasons": [
      "Corporate email detected",
      "Company provided (Acme Automacoes)",
      "Detailed context in description",
      "High-intent keywords found: api, automation, integration, urgent",
      "AI score adjustment (+16)"
    ],
    "ai_insights": {
      "score_delta": 16,
      "pain_point": "Manual sales workflow bottlenecks requiring API integration",
      "urgency": "High",
      "executive_summary": "High-fit B2B prospect with corporate domain and urgent automation timeline."
    },
    "summary": "[Auto-Qualification] Ana Silva (Acme Automacoes) -> Hot (100/100)..."
  },
  "synced_to_salesforce": true,
  "sync_status": "updated"
}
```

### OUTPUT EXAMPLE
<img width="1120" height="141" alt="image" src="https://github.com/user-attachments/assets/48630ddd-d7bd-4ece-8437-4587ee5127c2" />



<h2 align="center"><img src="https://api.iconify.design/lucide/sliders.svg?color=%23007ACC&width=26" alt="" /> Scoring Model & Thresholds</h2>

The qualification engine computes a deterministic baseline score first, then applies an optional bounded adjustment from Gemini (`score` is always clamped between `0` and `100`):

<table>
  <tr>
    <th>Signal / Criterion</th>
    <th>Weight</th>
    <th>Rule Logic</th>
  </tr>
  <tr>
    <td>Baseline Score</td>
    <td><code>+20</code></td>
    <td>Starting score for every valid inbound lead.</td>
  </tr>
  <tr>
    <td>Corporate Email Domain</td>
    <td><code>+25</code></td>
    <td>Awarded when domain is not a free provider (e.g. Gmail, Outlook, Yahoo).</td>
  </tr>
  <tr>
    <td>Company Provided</td>
    <td><code>+15</code></td>
    <td>Awarded when <code>Company</code> field is populated.</td>
  </tr>
  <tr>
    <td>Description Context</td>
    <td><code>+15</code></td>
    <td>Awarded when <code>Description</code> contains substantive context.</td>
  </tr>
  <tr>
    <td>High-Intent Keywords</td>
    <td><code>up to +25</code></td>
    <td>Matches commercial/technical buying signals (e.g. <code>api</code>, <code>automation</code>, <code>integration</code>, <code>urgent</code>).</td>
  </tr>
  <tr>
    <td>Gemini Semantic Adjustment</td>
    <td><code>-15 to +20</code></td>
    <td>Evaluates email-to-company alignment, pain point clarity, and urgency via structured schema.</td>
  </tr>
</table>

- **`Hot` (`70 - 100`):** Immediate sales follow-up priority.
- **`Warm` (`45 - 69`):** Qualified prospect for SDR nurturing.
- **`Cold` (`0 - 44`):** Low intent or incomplete B2B profile.

<h2 align="center"><img src="https://api.iconify.design/lucide/layers.svg?color=%23007ACC&width=26" alt="" /> Core Components</h2>

<table>
  <tr>
    <th>Module</th>
    <th>Responsibility</th>
  </tr>
  <tr>
    <td><code>src/config.py</code></td>
    <td>Type-safe environment configuration via <code>pydantic-settings</code>.</td>
  </tr>
  <tr>
    <td><code>src/salesforce_client.py</code></td>
    <td>OAuth2 Client Credentials auth, SOQL querying, and <code>PATCH</code> updates with <code>tenacity</code> retries.</td>
  </tr>
  <tr>
    <td><code>src/qualifier.py</code></td>
    <td>Hybrid engine combining rule-based scoring and <code>google-genai</code> structured schema outputs.</td>
  </tr>
  <tr>
    <td><code>src/main.py</code></td>
    <td>Idempotent batch runner for scheduled lead qualification jobs.</td>
  </tr>
  <tr>
    <td><code>src/api.py</code></td>
    <td><code>FastAPI</code> service exposing <code>GET /health</code> and <code>POST /qualify-lead</code> for real-time integrations.</td>
  </tr>
  <tr>
    <td><code>tests/test_qualifier.py</code></td>
    <td>Offline unit test suite (<code>pytest</code>) covering rules, AI enrichment mocks, and fallback behavior.</td>
  </tr>
</table>

<h2 align="center"><img src="https://api.iconify.design/lucide/terminal.svg?color=%23007ACC&width=26" alt="" /> Quickstart</h2>

```bash
# 1. Clone repository and create virtual environment
git clone [https://github.com/igorhsouza/salesforce-lead-qualifier.git](https://github.com/igorhsouza/salesforce-lead-qualifier.git)
cd salesforce-lead-qualifier
python -m venv .venv

# Activate virtual environment:
source .venv/bin/activate      # Linux / macOS
.venv\Scripts\Activate.ps1     # Windows PowerShell

# 2. Install dependencies and configure credentials
pip install -r requirements.txt
cp .env.example .env

# 3. Run offline unit tests
pytest

# 4. Run batch qualification or start FastAPI server
python -m src.main
uvicorn src.api:app --reload
```

<h2 align="center"><img src="https://api.iconify.design/lucide/activity.svg?color=%23007ACC&width=26" alt="" /> Observability & Production Deployment</h2>

- **Structured Logging:** Every module emits timestamped logs (`%(asctime)s | %(levelname)s | %(name)s | %(message)s`) tracking OAuth2 token acquisition, SOQL record counts, deterministic vs. AI score deltas, fallback warnings, and idempotent skips.
- **Batch Mode (Cron / VPS / Cloud Run Jobs):** Schedule `python -m src.main` every 5-15 minutes. Because the runner checks existing `Rating` and `Description` state before issuing `PATCH` calls, repeated executions are safe and incur zero redundant API writes.
- **Real-Time Mode (Cloud Run / Containerized VPS):** Deploy the Docker image (`uvicorn src.api:app --host 0.0.0.0 --port 8000`) behind an API gateway or reverse proxy and trigger `POST /qualify-lead` from a Salesforce Record-Triggered Flow (HTTP Callout) or an `n8n` webhook workflow.

```bash
docker build -t salesforce-lead-qualifier .
docker run --env-file .env -p 8000:8000 salesforce-lead-qualifier
docker run --env-file .env salesforce-lead-qualifier python -m src.main
```

<p align="center"><i>Rules first, AI where it adds value.</i></p>

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=110&section=footer&color=0:007ACC,100:001F3F&text=Built%20by%20Igor%20Henrique&fontColor=ffffff&fontSize=16&fontAlignY=45" alt="Footer" />
</p>
