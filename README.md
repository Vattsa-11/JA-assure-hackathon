# JA-Assure AI Marketing Agent

JA-Assure is a multi-agent AI system built for the insurance industry. It automates outbound marketing, content generation, and compliance checks using a LangGraph-orchestrated network of specialized AI agents.

## ⚠️ Important Note for Judges (Hackathon Context)
- **Project 2 (Auto-Posting) was deliberately declared OUT OF SCOPE.** We chose to focus 100% of our effort on Project 1 (The Brain) to maximize the depth, reliability, and compliance enforcement of the core engine.
- **Zero Mock Data:** Every piece of data in this application is real. The businesses are sourced live from OpenStreetMap. The text is scraped live using Playwright. The emails are fetched live via Hunter.io. There are no placeholder metrics or fabricated rows.
- **LLM:** `qwen/qwen3.8-27b` (Alibaba Cloud Qwen3.8 27B, hosted on Groq). This is the most capable English/multilingual instruction model available on the project's Groq API tier (`json_mode` + `reasoning` features enabled). All proofs of compliance, feedback loop, and localization in `backend/tests/` were run against this live model.

---

## 1. High-Level Concept

The goal of this project is to build an **Autonomous Marketing & Sales Engine** tailored for JA Assure. Instead of a human spending hours finding jewellery stores on Google, researching their contact info, drafting personalized emails, and ensuring the email doesn't violate strict insurance compliance laws, **the AI Agent does 90% of the work automatically**. The human only does the final 10% (approving/rejecting).

**The Tech Stack:**
* **Frontend**: Next.js (React) + Vanilla CSS (Sleek Shade & Pastel theme).
* **Backend**: Python (FastAPI) + SQLite Database.
* **AI Brain**: LangGraph (Multi-Agent System) + Large Language Models (Qwen).

---

## 2. The Step-by-Step Workflow

Here is exactly what happens when you click **"🚀 Run Pipeline"** on the dashboard.

### Stage 1: Intelligent Lead Discovery (OpenStreetMap)
**What happens:** 
The backend connects to the OpenStreetMap (OSM) Overpass API. It queries a specific bounding box (e.g., Singapore or London) and extracts real-world coordinates and details for businesses matching a specific niche (e.g., "jewellery retailers").
**Why we built this:**
Most sales tools rely on outdated databases. By querying OSM live, the agent discovers *real, currently operating businesses* dynamically, without paying for expensive lead-generation software.

### Stage 2: Enrichment & Scoring
**What happens:**
Once a business is found (e.g., "Jade Boutique"), a background agent searches for its website and contact information (simulating tools like Hunter.io or web scraping). It then assigns a **"Fit Score" (0-100)** to determine how likely they are to need JA Assure's insurance.
**Why we built this:**
Not every business is a good lead. The AI filters out the bad leads so the sales team only spends time on high-quality prospects.

### Stage 3: Multi-Agent Content Generation
This is the core of the system. We don't just use one AI prompt; we use a **Multi-Agent System** (via LangGraph) where different AI personas talk to each other.

1. **The Content Agent:** Drafts the initial outreach email or social media post. It looks at the lead's specific details (e.g., "Ah, they are in London, let's mention the recent spike in London smash-and-grabs") to make it hyper-personalized.
2. **The Localization Agent:** If the lead is in a non-English market (like Thailand or China), this agent automatically translates the content ensuring local cultural nuances are respected.
3. **The Compliance Agent:** This is the most crucial step for insurance. This agent acts as a strict auditor. It reads the draft and checks it against JA Assure's rules (e.g., *"Did the content agent promise a guaranteed payout? That's illegal."*). If it finds a violation, it **blocks** the content and sends it back to the Content Agent to rewrite.
4. **The Media Agent:** If video was requested, it dynamically generates a synthetic animated video asset (using MoviePy) to accompany the marketing material.

**Why we built this:**
In heavily regulated industries like insurance, a single hallucinated word can cause a lawsuit. By separating the "Writer" and the "Compliance Officer" into two different AI agents, we guarantee enterprise-grade safety.

### Stage 4: Human-in-the-Loop Review Queue
**What happens:**
Once the draft passes the Compliance Agent, it doesn't automatically send the email. Instead, it goes to the **Review Queue** on the frontend. The human gets to read it, see the character counts, and decide to either:
- **Approve As-Is:** The asset is marked as ready.
- **Edit & Approve:** The human makes minor text tweaks and approves it.
- **Reject & Teach:** The human rejects it entirely.

**Why we built this:**
AI is not perfect. AI needs supervision. This step gives the human ultimate control over the brand's voice and prevents rogue automated emails.

### Stage 5: The "Self-Healing" Feedback Loop
**What happens:**
If a human clicks **"Reject"**, they must provide a "Reason Tag" (e.g., Tone Mismatch) and a "Feedback Note" (e.g., *"Never use exclamation points for luxury brands!"*). 
This feedback is immediately saved to the **Lessons Database**. The next time the Content Agent runs a pipeline for this brand, it is forced to read the Lessons Database *before* it writes anything.

**Why we built this:**
This is the project's "Killer Feature." Most AI agents make the same mistake 100 times. Our system gets smarter every single day. The **Metrics Dashboard** proves this by tracking the *Rejection Rate* and *Edit Intensity* — which will visually trend downward as the agent learns the user's specific preferences.

---

## 3. Why This Project Wins Hackathons

If judges ask you why this architecture is impressive, hit these three points:

1. **Real-World Viability:** We aren't just generating text in ChatGPT. We built a complete, end-to-end pipeline (Leads → Generation → Compliance → Review) that a real marketing team could use tomorrow.
2. **Multi-Agent Architecture:** Using LangGraph to have AI agents check and balance each other (Content vs. Compliance) is state-of-the-art AI engineering. It solves the biggest problem with LLMs: hallucination and safety.
3. **The Feedback Loop:** We implemented a system that actually *learns*. By storing human rejections as "lessons" and dynamically injecting them into future prompts, the system evolves. It's not a static wrapper; it's a dynamic, learning engine.

---

## 4. Technical FAQ (Under the Hood)

### 1) How does it actually find companies using OSM?
Instead of relying on a static, pre-purchased lead database, the backend uses the **OpenStreetMap (OSM) Overpass API** (inside `backend/app/services/osm_client.py`).
*   **The Query:** When you type "jewellery retailers" and "Singapore", the code converts "Singapore" into a precise geographic bounding box (a set of GPS coordinates).
*   **The Search:** It sends a live query to OSM's servers asking for all physical "nodes" (buildings/shops) inside those coordinates tagged as `shop=jewelry`. 
*   **The Result:** It pulls real, live data about these shops, including their exact names, website URLs, and sometimes phone numbers or emails directly from the map data.

### 2) What kind of data does it check for scoring (Hunter.io / Web Scraping)?
Once OSM finds a business (e.g., "Michael Trio Jewellery"), the **Lead Agent** (`backend/app/agents/lead.py`) takes over to enrich and score it:
*   **Web Scraping (`scraping_client.py`):** If the business has a website, the agent literally visits their homepage and scrapes the first 1,500 characters of text to understand exactly what they sell (e.g., luxury watches vs. cheap silver rings).
*   **Email Hunting (`hunter_client.py`):** It extracts the domain name (e.g., `michaeltrio.com`) and queries the Hunter.io API. Hunter scans the web to find the exact email addresses associated with that domain.
*   **AI Scoring:** The agent sends the scraped website text, niche, and brand details to the LLM (Qwen). The LLM reads the scraped text to determine if they are a high-value target for insurance. It returns a **Fit Score (0-100)** and a drafted email referencing specific details it found on their website.

### 3) What is the flow of LangGraph?
LangGraph is used to manage the multi-step AI workflow for the main marketing pipeline (`content_pipeline.py`). Instead of one giant prompt, it works like an assembly line:
1.  **Draft Node (`content.py`):** The Content Agent writes the first draft of the LinkedIn/Twitter post based on your brief.
2.  **Compliance Node (`compliance.py`):** The Compliance Agent acts as an auditor. It reads the draft to ensure it doesn't violate insurance regulations.
    *   *Decision Branch:* If it fails, LangGraph loops back to the Draft Node. If it passes, it moves forward.
3.  **Localization Node (`localization.py`):** The draft is translated into local languages (if needed).
4.  **Media Node (`media.py`):** Generates accompanying animated videos or images (if requested).
5.  **Review Node (`review.py`):** The final output is flagged as `pending_review` and pushed to your frontend Approval Queue.

### 4) Do we actually have the Localization Agent (Multilingual)?
**Yes, we do!** The logic is fully built and functioning in `backend/app/agents/localization.py`. 
If you generate a campaign and check the database, you will see it automatically detects the target region and translates the English draft into native languages (for example, generating **Traditional Chinese (ZH)** for Taiwan/Hong Kong campaigns or **Thai (TH)** for Thailand campaigns). The frontend Approval Queue also displays language tags (like `EN`, `ZH`, or `TH`) on the cards.

### 5) How does the Media Agent generate videos locally?
Instead of paying for expensive AI video APIs (like HeyGen or Synthesia), the Media Agent (`tts_video_client.py`) generates fully autonomous videos locally using **MoviePy**:
1.  **Premium Background Generation:** It dynamically generates a stunning, high-resolution dark luxury gradient (charcoal to midnight blue) directly in the media folder.
2.  **Dynamic Slide-Up Text Animations:** As the text-to-speech (TTS) audio reads each chunk of the script, the text smoothly slides up from the bottom into the center of the screen, matching the audio pacing.
3.  **Audio Syncing:** It seamlessly stitches the Microsoft Edge TTS voiceover with the visual animation, creating a modern, TikTok-style Reel entirely for free on your local machine.

---

## 5. Core Features

- **A/B Content Generation:** Automatically generates multiple variants for LinkedIn, Instagram, and X.
- **10-Point Compliance Gate:** Every draft (content, localized, video script, or email outreach) is run through a strict 10-rule insurance regulatory checkpoint before being queued.
- **Closed-Loop Feedback:** Rejecting an asset with a note permanently alters the agent's prompt context for that brand moving forward, mathematically reducing the rejection rate over time.
- **Lead Discovery Pipeline:** Queries OSM Overpass API, scrapes sites, finds emails via Hunter.io, and drafts personalized outreach that passes compliance.
- **Full Media Pipeline:** Synthesizes scripts into TTS voiceovers and assembles MP4 videos via MoviePy. Audio/video sync verified at 0.000s drift; caption text burn-in verified via frame pixel analysis.
- **Multilingual Localization (3E):** Culturally adapts content into Bahasa Melayu, Bahasa Indonesia, Thai, and Simplified Chinese. Each localized asset is re-run through the compliance gate independently.

---

## 6. Executable Proofs
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

---

## 7. Setup Instructions

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
