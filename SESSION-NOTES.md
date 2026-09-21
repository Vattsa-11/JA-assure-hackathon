# Session Notes

Working log of UI improvements and maintenance performed on this repo. Newest entries first.

---

## 2026-09-21 — UI polish pass + maintenance

### Environment
- Repo pulled: already up to date (`5f44ef6`).
- Backend: `uvicorn app.main:app --reload` on :8000, run with workspace venv `../../.venv` (repo's own `venv/` is broken — points to an uninstalled Python 3.12).
- Frontend: `next dev` (Next 16, Turbopack) on :3000, logs to `backend.log` / `frontend.log` in repo root.
- Alembic migrations were already at head.

### Fixed
- **`.glass-panel` was missing from CSS** — used across pages but never defined; cards rendered flat. Added definition (white bg, soft border, hover lift).
- **Invisible "View / Edit" buttons** — white text on white cards. Now solid purple, full width.
- **Review modal** (queue + dashboard): added scale/slide animation, ✕ close button, platform-colored tags, language badge, char counter that turns red past platform limit, footer divider, helper text explaining the reject-and-teach loop.
- **Navbar**: extracted to `src/components/Navbar.tsx` (client component) with sticky glass background and active-route pill highlighting.
- **Queue page spacing**: added `.page-container` wrapper. Final layout = **5% padding on each edge (10% total), no max-width cap** (user request). Also applied to metrics and dashboard.
- **Oversized queue cards**: root cause was `display: flex` on `.queue-card-body` defeating `-webkit-line-clamp` (only works on `display: -webkit-box`). Cards now clamp to 6 lines; hook/body typography reduced for a more compact grid.
- **Metrics page**: KPI cards with gradient accent bars, `2.5rem 2rem` padding.
- **Dashboard**: removed the decorative dead sidebar (JA logo box + empty circle/square/dashed-circle shapes); page now uses `.page-container`.
- **Coral card inputs** (dashboard + leads): translucent white bg matching the coral gradient, white text/placeholder, white focus ring — global white input styles were overriding them due to CSS cascade order; fixed with a higher-specificity override placed after the global rules.

### Removed dead code
- `.line-clamp-4` CSS (unused after queue-card refactor; conflicted with `.queue-card-body` clamping).
- `inbox-row` className on dashboard feed rows (no matching CSS rule).
- `--accent-hover` CSS variable (unused).

### Added
- `.tag-warning` (referenced by dashboard "Requires Human" badge but missing).
- `btn-ghost`, `tag-platform-*` (x/twitter/linkedin/instagram/facebook/video/lead), `tag-language`, `.kpi-*`, `.page-container`, `.page-header`, `.modal-label`, `.modal-actions`, `.char-count(-over)`, `modalIn` keyframes.

### Endpoint verification (all live)
- GET: `/review/queue`, `/review/metrics`, `/review/leads`, `/dashboard/stats`, `/dashboard/brands`, `/dashboard/feed` → 200.
- POST: `/review/{id}/approve|edit|reject`, `/review/leads/{id}/approve|reject`, `/pipeline/content|leads|video/run` → exist; 404 on bad IDs, 422 on invalid payloads (expected validation behavior).

### Not done / ideas
- `.btn-white` uses `--accent` color; fine for now.
- Could add toast notifications instead of `alert()` for approve/reject errors.
