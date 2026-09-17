# JA-Assure Hackathon Demo Script

**Estimated Time**: 5-7 minutes
**Preparation**:
1. Ensure `.env` has a valid `GROQ_API_KEY`.
2. Ensure both backend and frontend servers are running.
3. Open `http://localhost:3000/queue` in a browser.

---

### Step 1: The Pitch & Architecture (1 min)
* "Hello judges. Marketing compliance is a huge bottleneck in the insurance industry. We built JA-Assure, a multi-agent system powered by LangGraph, to automate marketing while strictly enforcing compliance."
* *Show the Architecture slide or the codebase.*
* "We use specialized agents: a Content Engine to draft variants, a strict Compliance Agent to review them, and a Feedback Loop that learns from human approvals."

### Step 2: The Approval Queue (2 mins)
* *Open the Next.js Dashboard: `/queue`*
* "Here is the Human Approval Dashboard. Instead of writing copy from scratch, our marketing team reviews pre-generated, pre-localized, and pre-compliance-checked assets."
* *Action*: Click **Approve** on one asset.
* "When we approve, it's ready for publishing."
* *Action*: Click **Reject** on another asset. Select 'tone' and write: *"Make it sound more luxurious and premium."*
* "When we reject, we aren't just sending it back to draft. We are actively writing to our Feedback Loop database."

### Step 3: The Metrics & Feedback Loop (1 min)
* *Navigate to `/metrics`*
* "Because we just rejected that asset, our Rejection Rate metric updated live."
* "More importantly, the next time the Content Agent drafts copy for this brand, our Feedback Loop node automatically injects that exact rejection note into the prompt context. The agent literally learns not to make the same mistake twice, driving our edit intensity down over time."

### Step 4: Outbound Lead Gen (1 min)
* *Navigate to `/leads`*
* "We also built an outbound Lead Generation agent. It queries OpenStreetMap for local businesses (like jewelry shops in Singapore), enriches the data by scraping their websites, and drafts a highly personalized outbound email."
* *Action*: Show the fit score and the drafted email on the screen.

### Step 5: Wrap Up (1 min)
* "Everything you saw is running locally via our LangGraph StateGraphs, using LLaMA 3 via Groq for sub-second agent reasoning. Thank you!"
