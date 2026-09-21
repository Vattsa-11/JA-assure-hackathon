# JA-Assure Marketing Agent Demo Script

*Estimated time: 5-7 minutes*

## Prerequisites (Run 30 minutes before demo)
1. Ensure `.env` is populated with `GROQ_API_KEY` and `HUNTER_API_KEY`.
2. Ensure you have run:
   ```bash
   cd backend
   python -m alembic upgrade head
   python db/seed/seed_brands.py
   python db/seed/seed_demo.py
   ```
3. Start both backend and frontend servers:
   - Backend: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - Frontend: `npm run dev`

---

## 1. Introduction (30 seconds)
"Welcome to the JA-Assure Marketing Agent. Our solution is built entirely around an AI-driven, compliance-first architecture. 
Unlike standard 'content generators', everything here runs through strict regulatory compliance gates and features a closed-loop human feedback system.
No mock data is used; every lead and metric is generated dynamically."

## 2. The Dashboard & Queue (1 minute)
*Navigate to `localhost:3000/queue`*
"Here we see the Human Approval Dashboard. This queue contains content generated for our brands (like DoctorShield) that has **already passed** the automated compliance checks. You'll notice it generates platform-specific A/B variants automatically."

## 3. The Feedback Loop — THE WIN CONDITION (2 minutes)
"Let's demonstrate how the agent learns. I have a piece of content here for Jade."
*Action: Click 'Reject' on one of the items.*
"We are going to reject this because it's too salesy. I'll select the 'Tone' tag and write: *'Drop the urgency language and emojis. Be strictly professional, neutral, and corporate.'*"
*Action: Submit the rejection.*
"This note isn't just saved—it's injected directly into the LLM's context window the next time it writes for Jade, fundamentally altering its behavior. Let's look at the metrics."

## 4. The Metrics Dashboard (1 minute)
*Navigate to `localhost:3000/metrics`*
"Here we track the agent's learning progress. You can see our **Rejection Rate** and **Edit Intensity**. As humans reject content, the agent learns, and over time we expect these metrics to trend downward to zero."

## 5. Live Lead Generation — OSM & Scraping (1 minute)
*Navigate to `localhost:3000/leads`*
"Next, let's look at lead generation. We don't buy static lists. When we trigger this pipeline, it queries OpenStreetMap live for 'jewelry shops in Singapore'. It then scrapes their website, finds emails via Hunter.io, and scores their fit."
*Action: Show a lead.*
"You can see a real business name here, a dynamically calculated Fit Score based on their scraped 'About Us' page, and a highly personalized draft outreach email ready to be sent."

## 6. Closing (30 seconds)
"In conclusion, we have built a fully automated, strictly compliant, self-learning marketing engine. To maximize the depth and reliability of this 'Brain', we deliberately kept Project 2 (auto-posting) out of scope. Thank you."
