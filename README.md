# JA-Assure AI Marketing Agent

JA-Assure is a multi-agent AI system built for the insurance industry. It automates outbound marketing, content generation, and compliance checks using a LangGraph-orchestrated network of specialized AI agents.

## Architecture

This project is built using:
- **Backend**: FastAPI (Python), LangGraph, Llama-3 (via Groq), SQLite, SQLAlchemy
- **Frontend**: Next.js (React), Vanilla CSS (Glassmorphism design)
- **External Services**: 
  - OpenStreetMap (Overpass API) for business discovery
  - Hunter.io for email enrichment
  - Playwright for headless web scraping
  - Edge-TTS & MoviePy for Text-to-Speech Video Generation

## Features
- **Content Engine**: Generates multi-platform variants (LinkedIn, X, Instagram).
- **Compliance Agent**: Strictly evaluates content against legal rubrics.
- **Feedback Loop**: Agent automatically learns from human rejections in the UI.
- **Lead Generation**: Discovers real-world businesses, scrapes their sites, and drafts personalized outreach.
- **Multilingual Localization**: Culturally adapts content into regional languages.
- **Human Approval Dashboard**: A beautiful, real-time UI for marketing teams to approve or edit content.

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- A valid [Groq API Key](https://console.groq.com/)
- Optional: Hunter.io API Key (for lead enrichment)

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate | Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

### 3. Environment Variables
Create a `.env` file in the root directory:
```bash
cp .env.example .env
```
Fill in your `GROQ_API_KEY`.

### 4. Database Setup & Seeding
```bash
cd backend
alembic upgrade head
python db/seed/seed_brands.py
# Optional: generate real demo data (requires Groq API key)
python db/seed/seed_demo.py
```

### 5. Start Backend
```bash
cd backend
uvicorn app.main:app --reload
# Runs on http://localhost:8000
```

### 6. Start Frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```
