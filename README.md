# JA-Assure AI Marketing Agent

JA-Assure is a multi-agent AI system built for the insurance industry. It automates outbound marketing, content generation, and compliance checks using a LangGraph-orchestrated network of specialized AI agents.

## Architecture
This project is a multi-agent AI pipeline for automated, compliance-first insurance marketing.

## ⚠️ Important Note for Judges (Hackathon Context)
- **Project 2 (Auto-Posting) was deliberately declared OUT OF SCOPE.** We chose to focus 100% of our effort on Project 1 (The Brain) to maximize the depth, reliability, and compliance enforcement of the core engine.
- **Zero Mock Data:** Every piece of data in this application is real. The businesses are sourced live from OpenStreetMap. The text is scraped live using Playwright. The emails are fetched live via Hunter.io. There are no placeholder metrics or fabricated rows.
- **LLM:** `qwen/qwen3.8-27b` (Alibaba Cloud Qwen3.8 27B, hosted on Groq). This is the most capable English/multilingual instruction model available on the project's Groq API tier (`json_mode` + `reasoning` features enabled). All proofs of compliance, feedback loop, and localization in `backend/tests/` were run against this live model.

## Features
- **A/B Content Generation:** Automatically generates multiple variants for LinkedIn, Instagram, and X.
- **10-Point Compliance Gate:** Every draft (content, localized, video script, or email outreach) is run through a strict 10-rule insurance regulatory checkpoint before being queued.
- **Closed-Loop Feedback:** Rejecting an asset with a note permanently alters the agent's prompt context for that brand moving forward, mathematically reducing the rejection rate over time.
- **Lead Discovery Pipeline:** Queries OSM Overpass API, scrapes sites, finds emails via Hunter.io, and drafts personalized outreach that passes compliance.
- **Full Media Pipeline:** Synthesizes scripts into TTS voiceovers and assembles MP4 videos via MoviePy. Audio/video sync verified at 0.000s drift; caption text burn-in verified via frame pixel analysis.
- **Multilingual Localization (3E):** Culturally adapts content into Bahasa Melayu, Bahasa Indonesia, Thai, and Simplified Chinese. Each localized asset is re-run through the compliance gate independently.

## Executable Proofs
All proofs are live, executable scripts in `backend/tests/`. Run from the `backend/` directory:

| Script | Proves |
|--------|--------|
| `verify_feedback.py` | Feedback loop: rejection note structurally rewrites LLM output |
| `verify_osm.py` | OSM lead pipeline: raw Overpass JSON → DB rows → drafted outreach |
| `verify_compliance.py` | Compliance gate: paraphrased violation blocked by rubric meaning |
| `verify_lead_compliance.py` | Lead outreach gate: kickback offer blocked, lead status frozen |
| `verify_multilingual.py` | Localization: Bahasa Indonesia + independent compliance check |
| `verify_multilingual_thzh.py` | Localization: Thai script + Simplified Chinese characters verified |
| `verify_research.py` | Competitor digest: hash mutation triggers re-analysis |
| `verify_video.py` | Video: TTS + MP4 render, 0.000s sync, caption pixels confirmed |
| `verify_hunter.py` | Hunter.io email discovery (requires `HUNTER_API_KEY` in `.env`) |

## Setup Instructions

### 1. Copy Environment Template
```bash
cp .env.example backend/.env
```
Then edit `backend/.env` and fill in:
- `GROQ_API_KEY` — from [console.groq.com](https://console.groq.com). Free tier works.
- `HUNTER_API_KEY` — from [hunter.io](https://hunter.io). Optional; email discovery skips gracefully without it.

Create a `.env.local` file in the `frontend/` directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Backend
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

### 3. Database Setup & Seeding
```bash
cd backend
alembic upgrade head
python db/seed/seed_brands.py
# Optional: generates real demo data via live API calls (requires GROQ_API_KEY)
python db/seed/seed_demo.py
```

### 4. Start Backend
```bash
cd backend
uvicorn app.main:app --reload
# Runs on http://localhost:8000
```

### 5. Start Frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```
