<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=180&color=0:001F3F,50:0052A3,100:007ACC&text=Salesforce%20Lead%20Qualifier&fontColor=ffffff&fontSize=42&fontAlignY=38&desc=Hybrid%20B2B%20Lead%20Scoring%20%7C%20REST%20API%20and%20Gemini&descAlignY=62&descSize=16" alt="Salesforce Lead Qualifier" />
</p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&pause=1200&color=007ACC&center=true&vCenter=true&width=720&lines=Rules+first%2C+AI+where+it+adds+value;Deterministic+scoring+%2B+Gemini+structured+outputs;Idempotent+Salesforce+REST+API+sync;FastAPI+webhook+and+scheduled+batch+modes" alt="Typing animation" />
</p>

<p align="center">
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
      Explicit deterministic rules handle baseline scoring (0â€“100), while Gemini enriches leads with pain points, urgency, and executive summariesâ€”falling back safely if the LLM is unavailable.
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
        â”‚
        â–¼
  Pydantic Validation (LeadInput)
        â”‚
        â–¼
  Deterministic Scoring Engine (0â€“100 -> Hot / Warm / Cold)
        â”‚
        â–¼
  Gemini Structured Enrichment (AILeadInsights + Safe Fallback)
        â”‚
        â–¼
  Idempotency Check â”€â”€â–º Skip if Rating & Summary unchanged
        â”‚ (if changed)
        â–¼
  Salesforce REST PATCH (Updates Rating + Preserves Description)
```

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
# 1. Clone and activate virtual environment
git clone [https://github.com/igorhsouza/salesforce-lead-qualifier.git](https://github.com/igorhsouza/salesforce-lead-qualifier.git)
cd salesforce-lead-qualifier
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt

# 2. Configure credentials
cp .env.example .env

# 3. Run offline tests
pytest

# 4. Run batch qualification or start FastAPI server
python -m src.main
uvicorn src.api:app --reload
```

<h2 align="center"><img src="https://api.iconify.design/lucide/container.svg?color=%23007ACC&width=26" alt="" /> Docker Execution</h2>

```bash
docker build -t salesforce-lead-qualifier .
docker run --env-file .env -p 8000:8000 salesforce-lead-qualifier
docker run --env-file .env salesforce-lead-qualifier python -m src.main
```

<p align="center"><i>Rules first, AI where it adds value.</i></p>

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&height=110&section=footer&color=0:007ACC,100:001F3F&text=Built%20by%20Igor%20Henrique&fontColor=ffffff&fontSize=16&fontAlignY=45" alt="Footer" />
</p>

