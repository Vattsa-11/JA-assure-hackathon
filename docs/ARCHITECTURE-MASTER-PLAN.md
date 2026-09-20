# JA Assure AI Marketing Agent — Master Build Plan (TODO + Error Watchlist, Merged)

**Purpose:** Hand this whole file to your coding agent (Antigravity, Claude Code, Cursor, etc.) as its single working spec. It executes phase by phase, top to bottom. For each phase: do the build steps → run the verification checklist → check the "⚠️ Watch for" list before declaring the phase done → only then move on.

**Target:** Win by nailing Project 1 (The Brain) deeply — the compliance gate and closed-loop feedback learning are the explicit differentiator. **Project 2 (auto-posting) is out of scope** — all effort goes into Project 1.

**Locked decisions for this build:**
| Decision | Choice |
|---|---|
| Frontend | **Next.js** |
| Agent orchestration | **LangGraph** |
| Video/Reels scope | **Fully rendered** (script → TTS voiceover → assembled MP4) |
| Project 2 (auto-posting) | **Skipped entirely** — 100% focus on Project 1 |
| LLM provider | **Groq API** — coding agent picks the specific model per call type at build time |
| Lead data source | **100% real, zero mock data**: OpenStreetMap Overpass API + Playwright/BeautifulSoup scraping + Hunter.io free tier |
| Database | SQLite for local dev/demo, Postgres-ready via SQLAlchemy |

---

## GROUND RULES (apply everywhere, no exceptions)

1. Everything in code, version-controlled. No no-code tools. No notebooks as the deliverable.
2. Secrets only in `.env`, never hardcoded. Ship a `.env.example` with dummy values.
3. Nothing becomes "approved" without a human clicking Approve/Edit/Reject.
4. Every asset must pass the Compliance Agent before it reaches the human review queue.
5. **No mock/fake/placeholder data anywhere.** If a real source is unavailable, fail loudly — never fabricate data.
6. Unused/scratch files go to a gitignored `/_trash` folder — never delete outright, never leave dead code in main folders.
7. Commit after every phase with a clear message.
8. Do not proceed to the next phase until the current phase's verification passes.

---

## PHASE 0 — Environment & Repo Scaffold

**Do:**
- [ ] Create repo `ja-assure-marketing-agent/`, `git init`
- [ ] Folder structure:
  ```
  ja-assure-marketing-agent/
  ├── backend/
  │   ├── app/
  │   │   ├── agents/          # one file per agent, LangGraph nodes
  │   │   ├── graphs/          # LangGraph StateGraph definitions
  │   │   ├── api/              # FastAPI routers
  │   │   ├── models/           # SQLAlchemy DB models
  │   │   ├── schemas/          # Pydantic schemas
  │   │   ├── services/         # Groq client, scraping, OSM, Hunter, TTS/video
  │   │   ├── core/             # config, db session
  │   │   └── main.py
  │   ├── tests/
  │   ├── requirements.txt
  │   └── .env.example
  ├── frontend/                 # Next.js review dashboard
  ├── db/{migrations,seed}/
  ├── media/                    # generated video/audio
  ├── docs/ARCHITECTURE.md
  ├── _trash/                   # gitignored
  ├── .gitignore
  └── README.md
  ```
- [ ] `requirements.txt`: `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `pydantic-settings`, `groq`, `langgraph`, `langchain-groq`, `playwright`, `beautifulsoup4`, `requests`, `edge-tts`, `moviepy`, `pytest`
- [ ] `.gitignore`: `.env`, `venv/`, `node_modules/`, `__pycache__/`, `*.pyc`, `_trash/`, `.pytest_cache/`, `.next/`, `media/*.mp4`
- [ ] `.env.example`: `GROQ_API_KEY=`, `DATABASE_URL=sqlite:///./ja_assure.db`, `HUNTER_API_KEY=`

**Verify:**
- [ ] `git status` clean, matches structure above; `venv`/`node_modules` absent from tracked files
- [ ] `git grep -i "api_key.*="` matches only `.env.example` with blank values
- [ ] `pip install -r backend/requirements.txt` succeeds
- [ ] `python -m playwright install chromium` succeeds

**⚠️ Watch for:**
- `.env` not loaded → app runs but every LLM call fails with an auth error that looks like a network issue. Fail fast at startup if `GROQ_API_KEY` is missing.
- `.env` committed by accident — write `.gitignore` in the very first commit, before adding any files with secrets.
- Playwright installed but browser binaries not downloaded — `pip install playwright` alone is not enough; run the install command above or scraping fails with a cryptic "Executable doesn't exist" error.
- Python version mismatches across teammates' machines causing subtly different library behavior — pin a version in the README.
- Hardcoded `/` paths breaking on Windows — use `pathlib.Path` everywhere.
- `node_modules`/`venv` committed by accident — verify `.gitignore` catches these before the first commit.
- Port collisions (8000/3000 already in use on a teammate's machine) — document exact ports, check right before presenting.

---

## PHASE 1 — Database Schema (the spine)

**Do:**
- [ ] SQLAlchemy models: `Brand`, `ContentAsset` (with `source_asset_id` for localized versions, `status` enum), `ContentVersion`, `ComplianceReview`, `Feedback`/`Lesson`, `Lead`, `CompetitorDigestEntry`, `VideoAsset`
- [ ] Alembic initial migration for all tables
- [ ] `db/seed/seed_brands.py` — insert Jade, Jaguar Transit, DoctorShield with real written voice descriptions (2-3 sentences each)

**Verify:**
- [ ] `alembic upgrade head` — no errors; all 7 tables exist with correct columns
- [ ] Seed script → brands table returns exactly 3 rows
- [ ] `ContentAsset.status`/`Lead.status` reject invalid values at the app layer

**⚠️ Watch for:**
- Forgetting `alembic upgrade head` after a teammate's schema change → "no such column" errors that look like app bugs but are just stale schema.
- SQLite locks the whole file on write — don't run seed scripts while the API server is live and writing; "database is locked" errors will follow.
- Enum enforced only in Python, not at the DB level — a typo'd status string via a raw script insert creates an unqueryable "ghost" row nobody notices until demo day.
- Missing `ON DELETE CASCADE` — deleting a `ContentAsset` during testing leaves orphaned `ContentVersion`/`ComplianceReview` rows polluting later queries.
- Alembic autogenerate missing changes (SQLite has weaker ALTER TABLE support than Postgres) — manually diff generated migrations against model changes.
- Testing against a "dirty" DB — repeated demo runs without reset leave duplicate data that confuses judges. Keep a `reset_db.py` and run it before the real demo.

---

## PHASE 2 — Core Services

**Do:**
- [ ] `app/core/config.py` — pydantic-settings for `GROQ_API_KEY`, `DATABASE_URL`, `HUNTER_API_KEY`
- [ ] `app/services/llm_client.py` — Groq wrapper: system+user prompt, lessons-learned injection, structured/JSON-mode output for compliance. Let the agent pick the Groq model per call type.
- [ ] `app/services/scraping_client.py` — Playwright fetcher, graceful error handling, never fabricates data on failure
- [ ] `app/services/osm_client.py` — Overpass API wrapper (no key needed)
- [ ] `app/services/hunter_client.py` — Hunter.io free-tier wrapper
- [ ] `app/services/tts_video_client.py` — TTS synthesis + MoviePy assembly into rendered MP4
- [ ] `app/core/db.py` — engine + session factory
- [ ] Smoke tests per service

**Verify:**
- [ ] LLM smoke test returns real Groq text
- [ ] Renaming `.env` produces a clear "missing GROQ_API_KEY" error, not a silent crash
- [ ] OSM smoke test returns real jewellery-shop results for Singapore
- [ ] Playwright smoke test extracts text from one real page
- [ ] TTS smoke test produces a playable audio file

**⚠️ Watch for:**
- Groq free-tier rate limits — running the full pipeline back-to-back (content + compliance + 5-language localization + lead scoring + outreach + video script) can hit limits mid-demo. Add retry-with-backoff; know current limits before demo day.
- Model deprecation — keep the model name in config, not hardcoded, so it's a one-line fix if Groq retires a model.
- Non-JSON output when JSON is expected — LLMs sometimes wrap JSON in markdown fences or add a preamble sentence. Parse defensively; catch `JSONDecodeError`; re-prompt or fail loudly, don't crash.
- Prompt injection from scraped content — treat all scraped/fetched text as untrusted data in prompts, not instructions.
- Silent truncation of long scraped pages/context — chunk or pre-summarize long inputs before a final digest call.
- Defaulting every call to the largest model can slow the whole pipeline — reserve smaller/faster models for simple tasks (e.g. compliance pass/fail), larger ones for generation.
- Non-determinism causing flaky demos — test your exact demo prompts multiple times beforehand, not just once.

---

## PHASE 3 — Agents (as LangGraph nodes)

Structure each agent as a node on a shared pipeline state object; build and verify each independently before wiring into a `StateGraph`.

### 3A. Content Engine Agent (`app/agents/content.py`)

**Do:**
- [ ] `generate_content(state)` — injects brand voice + platform rules (LinkedIn professional/longer, Instagram visual caption, X short/hook-first)
- [ ] At least one A/B variant per platform; one idea → multiple formats (blog → carousel → tweet → caption)
- [ ] Save as `ContentAsset` rows, status = `draft`

**Verify:**
- [ ] Jade, "jewellery insurance for small retailers", 3 platforms → 6+ rows
- [ ] LinkedIn output visibly longer/more formal than X
- [ ] DoctorShield tone visibly more clinical/precise than Jade's

### 3B. Compliance Agent (`app/agents/compliance.py`)

**Do:**
- [ ] Compliance rubric (8-10 specific, checkable rules with example phrases — not vague vibes)
- [ ] `check_compliance(state)` — structured JSON: `{passed, flagged_phrases, reasons}`
- [ ] Save to `ComplianceReview`; failed stays `draft`, passed → `pending_review`

**Verify:**
- [ ] Bad sample ("guarantees 100% payout, always") → `passed=False` with specific flagged phrase
- [ ] Clean sample → `passed=True`
- [ ] Failed asset never reaches `pending_review`
- [ ] Write down 2-3 example pass/fail cases now for your demo script

**⚠️ Watch for:**
- Vague rubric phrasing → inconsistent judgment run to run. Write specific rules with example phrases.
- False negatives on paraphrased violations ("you can always count on full protection" vs the literal word "guaranteed") — explicitly instruct the LLM to check meaning/intent, not just keyword matching.
- Over-flagging killing your demo — calibrate against 5-10 test cases (clean and violating) before relying on it live.
- Forgetting to re-check after human edits — decide explicitly whether edits bypass or re-trigger compliance, and document the choice.
- Localized content bypassing compliance — a claim can become non-compliant only after translation; don't skip re-checking per language (handled in 3E).

### 3C. Human Approval Flow (data layer)

**Do:**
- [ ] `GET /review/queue`, `POST /review/{id}/approve`, `POST /review/{id}/edit` (creates `ContentVersion`), `POST /review/{id}/reject` (requires `reason_tag` + `note`, writes `Feedback`)

**Verify:**
- [ ] Each endpoint tested via `/docs`
- [ ] Reject without `reason_tag` → 422 validation error
- [ ] Reject creates a correctly linked `Feedback` row

### 3D. Feedback Loop (`app/agents/lessons.py`) — THE DIFFERENTIATOR

**Do:**
- [ ] `get_relevant_lessons(brand_id, limit=5)` — recent rejection/edit reasons+notes as "avoid this" bullets
- [ ] Inject into 3A's generation prompt before generating
- [ ] `get_rejection_rate()` and `get_edit_intensity()` metrics functions

**Verify:**
- [ ] Reject one asset with reason "too_salesy" + note "drop urgency language"
- [ ] Re-run on a similar topic → confirm new output actually avoids urgency language
- [ ] `get_rejection_rate()` returns a sane number
- [ ] Save this before/after pair — your single most important proof point

**⚠️ Watch for:**
- Lessons stored correctly but not actually changing output — the prompt-injection step either isn't reading them or the LLM ignores weak guidance. Read the actual generated output, don't just trust it's wired up.
- Lessons list growing unbounded — cap and dedupe (last 5 relevant), or injected context bloats and dilutes.
- Cross-brand contamination — a Jade lesson leaking into DoctorShield generation because the query isn't filtered by `brand_id`. Double-check the WHERE clause.
- Rejection-rate metric misleading with tiny sample sizes — "100% to 0%" from 3 data points is not a trend, be honest about sample size in your demo narrative.
- Metric calculated over a misleading time window — sanity-check the chart visually before demo day.

### 3E. Multilingual Agent (`app/agents/localization.py`)

**Do:**
- [ ] `localize_content(content_asset, target_language)` for `en, ms, id, th, zh` — explicit "localize, don't translate word-for-word" instruction
- [ ] New `ContentAsset` row with `source_asset_id` + `language` set
- [ ] Route each localized version through the Compliance Agent independently

**Verify:**
- [ ] All 5 languages generated for one asset
- [ ] Output structure/length differs sensibly per language, not identical structure copy-pasted
- [ ] Each localized version gets its own compliance check

**⚠️ Watch for:**
- Ambiguous language codes (`zh` = Simplified vs Traditional Chinese) — pin Simplified explicitly for this region's audience.
- Character encoding issues — Thai/Chinese/Bahasa text garbling if the DB column, API response, or Next.js page charset isn't UTF-8 end to end.
- Font fallback issues — confirm your dashboard's font stack actually renders Thai/Chinese glyphs, not fallback tofu boxes.
- "Localize not translate" evaluated inconsistently without a clear internal rubric — spot-check with a native speaker if at all possible.

### 3F. Lead Generation Agent (`app/agents/lead.py`) — 100% real data

**Do:**
- [ ] `find_leads(niche, region)`: query **OSM Overpass** for real businesses → for entries with a website, **Playwright/BeautifulSoup** fetch for enrichment text → for entries with a domain but no visible email, **Hunter.io free tier** for email discovery
- [ ] `score_lead(lead)` — explainable rubric (0-100, plain-text reason)
- [ ] `draft_outreach(lead, brand_id)` — personalized, references real business name/type, brand voice
- [ ] All failures return empty + clear log message — never fabricate a placeholder lead
- [ ] Leads/outreach go through the same approval flow

**Verify:**
- [ ] Jewellers, Singapore → real business names/addresses (cross-check one manually against OpenStreetMap/Google Maps)
- [ ] Fit_score has a visible, sensible reason
- [ ] Outreach draft references the specific real business name, not a generic template
- [ ] A nonsense niche/region returns empty + a clear log message, not fabricated leads

**⚠️ Watch for:**
- Public Overpass API rate limiting/timeouts, especially under shared venue wifi — cache successful results locally so a live demo doesn't depend on a live query working at that exact moment.
- Overpass QL syntax errors return an empty result set, not an error — indistinguishable from "no businesses found" unless you test queries in Overpass Turbo first.
- Scraping getting blocked by bot detection — use realistic user-agent headers, reasonable delays, and have 2-3 backup directory sources.
- Hunter.io free-tier quota exhaustion from repeated testing — track usage, stop casually re-running this call once confirmed working.
- Messy scraped text (ads, cookie banners, nav text mixed into "content") — clean/strip before feeding to the LLM for enrichment.
- Legal/ethical scraping boundaries — stick to sites that clearly allow it or have public APIs; don't scrape LinkedIn directly (against ToS, commonly blocked).
- Genuinely obscure niche+region combos correctly returning zero results looks like a bug live — pre-test your exact demo query well in advance to confirm it reliably returns real results.

### 3G. Video/Reels Agent (`app/agents/media.py`) — fully rendered

**Do:**
- [ ] `generate_video_script(topic, brand_id)` → `{script, scene_breakdown, caption_text, voiceover_tone}`
- [ ] `synthesize_voiceover(script)` via `edge-tts` or similar free TTS
- [ ] `assemble_video(...)` via MoviePy — text-overlay/visuals + timed captions + voiceover track → `.mp4`
- [ ] Save to `VideoAsset`, link to a `ContentAsset` (format=`video_script`), route script text through compliance too

**Verify:**
- [ ] Playable `.mp4` produced in `media/`
- [ ] Audio and captions in sync, matching the script
- [ ] Video's script text was checked by the Compliance Agent before being marked ready for review

**⚠️ Watch for:**
- Audio/caption desync — if caption timing is word-count-estimated rather than derived from actual TTS duration, captions drift, especially on longer scripts. Prefer engines that return timestamps, or measure actual audio duration.
- MoviePy version incompatibilities — API has had breaking changes (especially `TextClip`/font-finding). Pin a specific version and confirm your exact code works with it.
- Missing system fonts on the demo laptop — often the first thing that breaks moving from dev machine to demo machine. Test the render on the actual demo machine in advance.
- Render time surprise — video assembly is much slower than text generation. Don't trigger a fresh render live during judging unless timed; consider pre-rendering the demo example.
- Generated `.mp4`s committed to git instead of gitignored — bloats repo, slows clone/pull.
- TTS voice/language coverage gaps — confirm your chosen free TTS actually supports Thai/Bahasa/Chinese, not just English, before relying on it.

### 3H. Competitor Intelligence Agent (`app/agents/research.py`)

**Do:**
- [ ] `run_competitor_digest(competitor_urls)` — fetch via Playwright, diff against last snapshot (text hash), summarize changes via Groq with a suggested action
- [ ] Store snapshot for next-run diffing

**Verify:**
- [ ] 2-3 real public competitor pages
- [ ] Second run detects and meaningfully summarizes real changes
- [ ] Digest gives a specific, readable suggested action

**⚠️ Watch for:**
- Scraping targets changing structure mid-hackathon breaking brittle selectors — prefer LLM-based content extraction over CSS selectors where possible.
- No baseline on first run — handle gracefully as "first snapshot, no digest yet," don't crash on a missing comparison file.
- False "changes" from dynamic page content (ads, timestamps, randomized ordering) — strip obviously dynamic elements before hashing/diffing.

**Phase 3 overall verification:**
- [ ] All 7 agent files pass their own verification
- [ ] `pytest` green across unit tests
- [ ] Commit: `git commit -m "feat: phase 3 - all core agents built and verified"`

---

## PHASE 4 — LangGraph Pipeline Wiring

**Do:**
- [ ] `app/graphs/content_pipeline.py` — `StateGraph`: generate → compliance check → conditional edge (pass → `pending_review`; fail → end/log), lessons injection inside the generate node
- [ ] `app/graphs/lead_pipeline.py` — find leads → score → draft outreach → compliance check → `pending_review`
- [ ] API endpoints: `POST /pipeline/content/run`, `POST /pipeline/leads/run`

**Verify:**
- [ ] Content graph run end-to-end via API — DB rows move draft → compliance_checked → pending_review correctly
- [ ] Lead graph run end-to-end, same check
- [ ] Force a compliance failure mid-graph — that asset halts correctly, without crashing the whole run

**⚠️ Watch for:**
- Mutating shared state in place instead of returning updates — LangGraph's state-merging can silently drop/overwrite fields from parallel branches.
- Missing conditional edges for the "compliance failed" path — no edge means the graph errors or silently dead-ends. Always wire an explicit failed/end path.
- Infinite loops if you build a "revise until compliant" retry — always cap retries (e.g. max 3), or you can burn your entire Groq quota in seconds.
- Graph state not persisted before a crash — mid-graph process crashes can leave assets in an inconsistent status if node writes aren't atomic.
- LangGraph API/version drift — pin the version in `requirements.txt` so a mid-hackathon upgrade doesn't break your graph definitions.

---

## PHASE 5 — Next.js Human Approval Dashboard

**Do:**
- [ ] Pages: `/queue` (pending_review content + leads), detail view (Approve/Edit/Reject with reason_tag+note), `/metrics` (rejection rate, edit intensity trend), `/leads` (real scored leads + outreach drafts)
- [ ] Wire to FastAPI endpoints

**Verify:**
- [ ] `/queue` renders real DB data
- [ ] Approve/Reject/Edit all correctly update DB and disappear from queue
- [ ] `/metrics` numbers change after test approvals/rejections
- [ ] `/leads` shows real scraped/OSM-sourced leads
- [ ] No console errors during a full click-through

**⚠️ Watch for:**
- CORS errors — FastAPI blocking `localhost:3000` requests by default. Add explicit CORS middleware.
- Hardcoded API base URL — use `.env.local` for the frontend's API base so it doesn't silently fail on a different machine/port.
- Stale data after mutation — approve/reject not refetching the queue makes it look like nothing happened. Refetch or optimistic-update after every action.
- Next.js App Router server/client component confusion — hydration mismatches from data-fetching logic in the wrong component type.
- Missing loading/error states — a slow LLM-backed API call with a blank screen looks broken to judges even when it's working normally.

---

## PHASE 6 — Seed Data & Demo Readiness

**Do:**
- [ ] `db/seed/seed_demo.py` — populate by actually running the real pipelines once (not fabricated rows), including at least one real rejection with feedback so `/metrics` isn't empty
- [ ] `docs/DEMO_SCRIPT.md` — exact click-by-click steps with expected results
- [ ] Test the full demo script on a clean DB at least twice

**Verify:**
- [ ] Wipe DB, re-run migrations + real seed, dashboard loads with real data
- [ ] Run through `DEMO_SCRIPT.md` yourself — 5-7 minutes
- [ ] A teammate runs it independently without help — fix anything that confuses them

**⚠️ Watch for:**
- Running the demo on a laptop that's never been tested end-to-end — different Python version, missing Playwright browsers, missing video fonts. Do a full clean-clone-and-run rehearsal on the exact presenting machine.
- No internet at the venue breaking Groq/Overpass/Hunter/scraping live — have a pre-recorded backup video of one full successful run, and a pre-cached working demo dataset so you can show the dashboard/metrics even if live generation fails.
- Live generation being slow eating your demo time slot — have already-completed example runs in the DB to show alongside one live generation.

---

## PHASE 7 — Final Polish & Submission Readiness

**Do:**
- [ ] Sweep every folder, move unused/experimental files into `_trash/`
- [ ] Confirm `_trash/` gitignored
- [ ] Final `README.md`: what it does, architecture diagram, setup instructions, explicit note that Project 2 was out of scope by design, explicit note that all data is real/live with no mocks
- [ ] Final secrets check: `git grep -iE "(api[_-]?key|secret|password)\s*=\s*['\"][a-zA-Z0-9]"` returns nothing except `.env.example` placeholders
- [ ] Confirm `.env` not tracked: `git ls-files | grep "^\.env$"` returns nothing

**Verify (final acceptance checklist):**
- [ ] Fresh clone + fresh `.env` with real keys → works end to end following only the README
- [ ] Compliance gate demonstrably blocks a bad claim (test case ready)
- [ ] Feedback loop demonstrably changes output after rejection (before/after pair ready)
- [ ] Brand voice visibly different across Jade / DoctorShield / Jaguar Transit
- [ ] 3 platforms show distinct formatting
- [ ] 2+ languages localized (not translated), each independently compliance-checked
- [ ] Lead list shows real, verifiable businesses with scored fit + real drafted outreach
- [ ] Rendered video plays with synced audio/captions
- [ ] Dashboard approve/edit/reject all work live
- [ ] Metrics page shows a real trend from real runs
- [ ] No hardcoded secrets anywhere; no stray/dead files in main folders
- [ ] README accurate, states Project 2 was skipped by design and why

**⚠️ Watch for:**
- API keys leaking client-side — any Groq/Hunter calls accidentally made from Next.js instead of proxied through FastAPI exposes your key in the browser network tab. All external API calls must be server-side only.
- `.env.example` accidentally containing a real key (copy-paste mistake) — double-check this specific file before every push.
- Debug mode left on — leaks stack traces/file paths if a judge triggers an error while poking at the API directly. Turn off verbose error responses before presenting.
- Overclaiming during the pitch (e.g. "fully automated across all 5 countries" when only Singapore was tested) — state exactly what's proven vs architecturally supported but untested.
- README/setup untested by someone else — if judges try to run it from the README and it fails on step 2, that's a direct hit on the "craft" criterion. Get an outsider to follow it from a clean environment before submission.
- Leftover debug `print()`s, dead commented-out code, messy naming — costs real points on "craft" even with perfect functionality. Don't skip this pass under time pressure.

---

## Demo Day Order of Operations

1. Architecture diagram (30 sec) — one DB table is the spine, LangGraph agents write/read from it
2. Live content generation run → land in queue
3. Compliance gate catching a bad claim live
4. Reject one item with a reason live
5. Re-run on a similar topic → show it avoiding the mistake (**win condition**)
6. Metrics page trending correctly
7. Real lead + real outreach draft, with the business name shown as verifiably real
8. One localized asset
9. Play the rendered video with synced voiceover/captions
10. End with README/repo structure, and a one-line honest note that Project 2 was deliberately out of scope to maximize Project 1 depth

## Quick Pre-Demo Sanity Checklist (run 30 minutes before presenting)

- [ ] Fresh DB reset + real seed run completed successfully
- [ ] Backend and frontend both start cleanly with no console errors
- [ ] One full pipeline run (content → compliance → review → reject → regenerate) tested in the last hour, on the actual demo machine, on the actual venue network
- [ ] Video sample pre-rendered and confirmed playable
- [ ] Lead query for your exact demo niche/region confirmed to return real results right now (not just "it worked yesterday")
- [ ] No `.env` values visible on screen if you share your terminal/editor
- [ ] Backup: one screen-recorded video of a full successful run, in case live demo fails
- [ ] README re-read once, out loud, to catch any remaining inaccuracies

Good luck — the compliance gate + feedback loop combo, backed by fully real data throughout, done well and demoed live, is what separates a "captions generator" from an actual win.
