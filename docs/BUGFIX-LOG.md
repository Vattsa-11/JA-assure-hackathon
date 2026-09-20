# error_till_now.md

> ## ✅ UPDATE — mypy errors fixed (2026-09-19)
> All **26 mypy errors are now fixed** (`mypy app` → `Success: no issues found in 36 source files`).
> Ruff incidental reduction: 92 → 77 (style-only; not the goal of this pass, and none introduced).
>
> **What was changed (see git diff for details):**
> 1. **`app/models/lead.py` — the real runtime bug:** added missing `LeadStatus.rejected` member. Verified live: `POST /review/leads/{id}/reject` went from **HTTP 500 (`AttributeError: rejected`) → HTTP 200**, status persists as `rejected` in DB.
> 2. **All models + `models/base.py`** converted from legacy `Column(...)` to SQLAlchemy 2.0 `Mapped[...] / mapped_column(...)` — resolves all `Column[Any]` assignment/arg-type errors.
> 3. **`app/services/llm_client.py`:** `ChatGroq(groq_api_key=..., model_name=...)` → `ChatGroq(api_key=SecretStr(...), model=...)` (langchain-groq v1.1 field names); added `_content_str()` helper to handle `str | list` AIMessage content; added explicit `raise RuntimeError` after retry loops (fixes both "Missing return statement" errors and the real None-on-exhausted-retries logic gap).
> 4. **`app/core/config.py`:** `GROQ_API_KEY: str | None = None` + explicit `RuntimeError` at import if missing (fail-fast behavior preserved, type-checker satisfied).
> 5. **`app/services/hunter_client.py`:** typed `params: dict[str, str | int]` (fixes `requests.get` arg-type).
> 6. **`app/services/tts_video_client.py`:** `MOVIEPY_V2` is now strictly `bool` (was `True/False/None` — the None→bool assignment bug); moviepy imports carry `type: ignore[no-redef]` for the v1 fallback path.
> 7. **`app/api/pipeline.py`:** initial states typed as `ContentState` / `LeadState` TypedDicts (fixes both LangGraph `invoke` overload errors); removed unused `HTTPException` import; added the missing `passed_lead_ids`/`failed_lead_ids` keys the `LeadState` TypedDict requires.
> 8. **`app/api/dashboard.py`:** `feed.sort(key=lambda x: str(x["created_at"]))` (fixes sort-key arg-type).
> 9. **Project structure:** added missing `app/__init__.py`, `app/agents/__init__.py`, `app/api/__init__.py`, `app/core/__init__.py`, `app/graphs/__init__.py`, `app/schemas/__init__.py`, `app/services/__init__.py` (mypy duplicate-module abort no longer occurs — though `--explicit-package-bases` is still used via `mypy.ini`); added root `mypy.ini` (`explicit_package_bases`, `mypy_path=backend`, moviepy import ignore).
> 10. Backend restarted and verified: `/`, `/dashboard/stats`, `/review/queue` all 200; frontend (:3000) unaffected.
>
> **Note:** `ja-assure-marketing-agent/backend/app/` still contains the *unfixed* copies of these files (it was left untouched).

---

## Original report (before fixes)

**Generated:** 2026-09-19
**Scope:** `ja-assure-submission/backend/app/` (32 source files).
Note: `ja-assure-marketing-agent/backend/app/` is byte-identical to it (`diff -rq` → no differences), so these results apply to both copies.
**Tools:** ruff 0.16.8, mypy 2.3.1 (Python 3.11 venv). **No fixes were applied** — findings only.

---

## 1. Ruff — 92 errors (65 auto-fixable with `--fix`)

Command: `ruff check app` (run from `backend/`)

### Summary by rule

| Rule | Count | Meaning |
|---|---|---|
| I001 | 34 | Import block is un-sorted or un-formatted |
| BLE001 | 12 | Do not catch blind exception: `Exception` |
| B008 | 11 | Do not perform function call `Depends()` in argument defaults (FastAPI pattern — false-positive-ish, but flagged) |
| UP045 | 6 | Use `X \| None` instead of `Optional[X]` |
| UP006 | 6 | Use `list`/`dict` instead of `List`/`Dict` |
| UP035 | 5 | `typing.List`/`typing.Dict` is deprecated |
| RUF010 | 10 | Use explicit conversion flag in f-strings (e.g. `{str(x)}` → `{x!s}`) |
| F401 | 3 | Imported but unused: `sqlalchemy.func` (lessons.py:2), `fastapi.HTTPException` (api/pipeline.py:1), `typing.Optional` (services/llm_client.py:2) |
| RUF022 | 1 | `__all__` is not sorted (models/__init__.py:8) |

### Full list

```
app\agents\compliance.py:1:1: I001 Import block is un-sorted or un-formatted
app\agents\content.py:1:1: I001 Import block is un-sorted or un-formatted
app\agents\lead.py:1:1: I001 Import block is un-sorted or un-formatted
app\agents\lead.py:82:16: BLE001 Do not catch blind exception: `Exception`
app\agents\lessons.py:1:1: I001 Import block is un-sorted or un-formatted
app\agents\lessons.py:2:24: F401 `sqlalchemy.func` imported but unused
app\agents\lessons.py:4:1: UP035 `typing.List` is deprecated, use `list` instead
app\agents\lessons.py:6:73: UP006 Use `list` instead of `List` for type annotation
app\agents\localization.py:1:1: I001 Import block is un-sorted or un-formatted
app\agents\media.py:1:1: I001 Import block is un-sorted or un-formatted
app\agents\research.py:1:1: I001 Import block is un-sorted or un-formatted
app\api\dashboard.py:1:1: I001 Import block is un-sorted or un-formatted
app\api\dashboard.py:13:29: B008 Do not perform function call `Depends` in argument defaults
app\api\dashboard.py:36:30: B008 Do not perform function call `Depends` in argument defaults
app\api\dashboard.py:41:28: B008 Do not perform function call `Depends` in argument defaults
app\api\pipeline.py:1:1: I001 Import block is un-sorted or un-formatted
app\api\pipeline.py:1:49: F401 `fastapi.HTTPException` imported but unused
app\api\pipeline.py:57:9: I001 Import block is un-sorted or un-formatted
app\api\pipeline.py:62:16: BLE001 Do not catch blind exception: `Exception`
app\api\pipeline.py:73:9: I001 Import block is un-sorted or un-formatted
app\api\pipeline.py:79:16: BLE001 Do not catch blind exception: `Exception`
app\api\review.py:1:1: I001 Import block is un-sorted or un-formatted
app\api\review.py:10:36: B008 Do not perform function call `Depends` in argument defaults
app\api\review.py:28:48: B008 Do not perform function call `Depends` in argument defaults
app\api\review.py:38:67: B008 Do not perform function call `Depends` in argument defaults
app\api\review.py:50:71: B008 Do not perform function call `Depends` in argument defaults
app\api\review.py:67:31: B008 Do not perform function call `Depends` in argument defaults
app\api\review.py:68:5: I001 Import block is un-sorted or un-formatted
app\api\review.py:75:29: B008 Do not perform function call `Depends` in argument defaults
app\api\review.py:82:46: B008 Do not perform function call `Depends` in argument defaults
app\api\review.py:92:45: B008 Do not perform function call `Depends` in argument defaults
app\core\config.py:1:1: I001 Import block is un-sorted or un-formatted
app\core\db.py:1:1: I001 Import block is un-sorted or un-formatted
app\graphs\content_pipeline.py:1:1: UP035 `typing.List` is deprecated, use `list` instead
app\graphs\content_pipeline.py:1:1: I001 Import block is un-sorted or un-formatted
app\graphs\content_pipeline.py:13:26: UP006 Use `list` instead of `List` for type annotation
app\graphs\content_pipeline.py:14:23: UP006 Use `list` instead of `List` for type annotation
app\graphs\content_pipeline.py:15:23: UP006 Use `list` instead of `List` for type annotation
app\graphs\content_pipeline.py:39:20: BLE001 Do not catch blind exception: `Exception`
app\graphs\lead_pipeline.py:1:1: I001 Import block is un-sorted or un-formatted
app\graphs\lead_pipeline.py:40:20: BLE001 Do not catch blind exception: `Exception`
app\main.py:1:1: I001 Import block is un-sorted or un-formatted
app\main.py:17:1: I001 Import block is un-sorted or un-formatted
app\models\__init__.py:1:1: I001 Import block is un-sorted or un-formatted
app\models\__init__.py:8:11: RUF022 `__all__` is not sorted
app\models\base.py:1:1: I001 Import block is un-sorted or un-formatted
app\models\brand.py:1:1: I001 Import block is un-sorted or un-formatted
app\models\content.py:1:1: I001 Import block is un-sorted or un-formatted
app\models\lead.py:1:1: I001 Import block is un-sorted or un-formatted
app\models\media.py:1:1: I001 Import block is un-sorted or un-formatted
app\models\research.py:1:1: I001 Import block is un-sorted or un-formatted
app\schemas\pipeline.py:1:1: I001 Import block is un-sorted or un-formatted
app\schemas\review.py:1:1: I001 Import block is un-sorted or un-formatted
app\schemas\review.py:7:14: UP045 Use `X | None` for type annotations
app\schemas\review.py:8:12: UP045 Use `X | None` for type annotations
app\schemas\review.py:11:16: UP045 Use `X | None` for type annotations
app\schemas\review.py:12:17: UP045 Use `X | None` for type annotations
app\schemas\review.py:13:21: UP045 Use `X | None` for type annotations
app\services\hunter_client.py:1:1: I001 Import block is un-sorted or un-formatted
app\services\hunter_client.py:12:53: UP045 Use `X | None` for type annotations
app\services\hunter_client.py:34:78: RUF010 Use explicit conversion flag
app\services\hunter_client.py:36:16: BLE001 Do not catch blind exception: `Exception`
app\services\hunter_client.py:37:64: RUF010 Use explicit conversion flag
app\services\llm_client.py:1:1: I001 Import block is un-sorted or un-formatted
app\services\llm_client.py:2:1: UP035 `typing.Dict` is deprecated, use `dict` instead
app\services\llm_client.py:2:31: F401 `typing.Optional` imported but unused
app\services\llm_client.py:44:150: RUF010 Use explicit conversion flag
app\services\llm_client.py:47:85: RUF010 Use explicit conversion flag
app\services\llm_client.py:50:186: UP006 Use `dict` instead of `Dict` for type annotation
app\services\llm_client.py:71:80: RUF010 Use explicit conversion flag
app\services\llm_client.py:77:150: RUF010 Use explicit conversion flag
app\services\llm_client.py:80:94: RUF010 Use explicit conversion flag
app\services\osm_client.py:1:1: I001 Import block is un-sorted or un-formatted
app\services\osm_client.py:3:1: UP035 `typing.List` is deprecated, use `list` instead
app\services\osm_client.py:3:1: UP035 `typing.Dict` is deprecated, use `dict` instead
app\services\osm_client.py:11:75: UP006 Use `list` instead of `List` for type annotation
app\services\osm_client.py:11:80: UP006 Use `dict` instead of `Dict` for type annotation
app\services\osm_client.py:64:137: RUF010 Use explicit conversion flag
app\services\osm_client.py:67:99: RUF010 Use explicit conversion flag
app\services\osm_client.py:69:20: BLE001 Do not catch blind exception: `Exception`
app\services\osm_client.py:70:65: RUF010 Use explicit conversion flag
app\services\scraping_client.py:1:1: I001 Import block is un-sorted or un-formatted
app\services\scraping_client.py:41:16: BLE001 Do not catch blind exception: `Exception`
app\services\scraping_client.py:42:55: RUF010 Use explicit conversion flag
app\services\tts_video_client.py:1:1: I001 Import block is un-sorted or un-formatted
app\services\tts_video_client.py:11:5: I001 Import block is un-sorted or un-formatted
app\services\tts_video_client.py:15:9: I001 Import block is un-sorted or un-formatted
app\services\tts_video_client.py:36:16: BLE001 Do not catch blind exception: `Exception`
app\services\tts_video_client.py:37:59: RUF010 Use explicit conversion flag
app\services\tts_video_client.py:111:24: BLE001 Do not catch blind exception: `Exception`
app\services\tts_video_client.py:133:16: BLE001 Do not catch blind exception: `Exception`
app\services\tts_video_client.py:134:55: RUF010 Use explicit conversion flag
```

---

## 2. mypy — 26 errors in 12 files (32 files checked)

Command: `mypy --explicit-package-bases app` (run from `backend/`; without that flag mypy aborts with
`Duplicate module named "pipeline"` because `app/schemas/pipeline.py` and `app/api/pipeline.py` share a basename
and the packages lack consistent `__init__.py` visibility — that itself is a structural issue worth noting).

### Full list

```
app\core\config.py:15: error: Missing named argument "GROQ_API_KEY" for "Settings"  [call-arg]
app\services\hunter_client.py:20: error: Argument "params" to "get" has incompatible type "dict[str, object]"; expected mapping/iterable of str types  [arg-type]
app\models\lead.py:21: error: Need type annotation for "status"  [var-annotated]
app\models\content.py:18: error: Need type annotation for "status"  [var-annotated]
app\services\tts_video_client.py:11: error: Skipping analyzing "moviepy": module is installed, but missing library stubs or py.typed marker  [import-untyped]
app\services\tts_video_client.py:15: error: Skipping analyzing "moviepy.editor": module is installed, but missing library stubs or py.typed marker  [import-untyped]
app\services\tts_video_client.py:18: error: Incompatible types in assignment (expression has type "None", variable has type "bool")  [assignment]
app\api\review.py:33: error: Incompatible types in assignment (expression has type "ContentStatus", variable has type "Column[Any]")  [assignment]
app\api\review.py:45: error: Incompatible types in assignment (expression has type "ContentStatus", variable has type "Column[Any]")  [assignment]
app\api\review.py:62: error: Incompatible types in assignment (expression has type "ContentStatus", variable has type "Column[Any]")  [assignment]
app\api\review.py:87: error: Incompatible types in assignment (expression has type "LeadStatus", variable has type "Column[Any]")  [assignment]
app\api\review.py:97: error: "type[LeadStatus]" has no attribute "rejected"  [attr-defined]
app\api\dashboard.py:56: error: Argument 2 to "get_relevant_lessons" has incompatible type "Column[int]"; expected "int"  [arg-type]
app\services\llm_client.py:16: error: Unexpected keyword argument "groq_api_key" for "ChatGroq"  [call-arg]
app\services\llm_client.py:16: error: Unexpected keyword argument "model_name" for "ChatGroq"  [call-arg]
app\services\llm_client.py:22: error: Incompatible types in assignment (expression has type "_ChatModelBinding", variable has type "ChatGroq")  [assignment]
app\services\llm_client.py:25: error: Missing return statement  [return]
app\services\llm_client.py:50: error: Missing return statement  [return]
app\agents\compliance.py:69: error: Incompatible types in assignment (expression has type "ContentStatus", variable has type "Column[Any]")  [assignment]
app\agents\compliance.py:118: error: Incompatible types in assignment (expression has type "LeadStatus", variable has type "Column[Any]")  [assignment]
app\agents\media.py:48: error: Argument 2 to "check_compliance" has incompatible type "Column[int]"; expected "int"  [arg-type]
app\agents\media.py:61: error: Argument "bg_color" to "assemble_video" has incompatible type "Column[str]"; expected "str"  [arg-type]
app\agents\localization.py:51: error: Argument "prompt" to "generate_text" has incompatible type "Column[str]"; expected "str"  [arg-type]
app\agents\localization.py:80: error: Argument 2 to "check_compliance" has incompatible type "Column[int]"; expected "int"  [arg-type]
app\api\pipeline.py:18: error: No overload variant of "invoke" of "Pregel" matches argument type "dict[str, object]"  [call-overload]
app\api\pipeline.py:31: error: No overload variant of "invoke" of "Pregel" matches argument type "dict[str, object]"  [call-overload]
```

### Interpretation notes (no fixes applied)

- **`app/api/review.py:97` — `"type[LeadStatus]" has no attribute "rejected"`** is the most likely *real runtime bug* in the list: `LeadStatus` in `app/models/lead.py` may not define a `rejected` member, which would raise `AttributeError` when rejecting a lead via `POST /review/leads/{id}/reject`. Worth verifying manually.
- The many **`Column[Any]` assignment / `Column[int]` arg-type** errors are the classic un-migrated SQLAlchemy 1.x-style model declarations being checked under SQLAlchemy 2.0 stubs (models use `Column(...)` without `Mapped[...]` annotations). They are type-checker noise at runtime, but they mask genuine typing.
- **`llm_client.py` ChatGroq kwargs + `_ChatModelBinding` + missing returns**: `generate_text`/`generate_json` can implicitly return `None` if the retry loop exhausts without raising (the `raise` is inside the `else` branch), and `model.bind(...)` changes the static type. Runtime risk is low but the missing-return paths are real logic gaps on exhausted retries.
- **`tts_video_client.py:18`** assigns `None` to a variable previously typed `bool` — a latent `Optional` bug.
- **`config.py:15`** missing-argument error is a pydantic-settings false positive at type level (env provides the value at runtime), but it also means mypy cannot prove startup fails fast without `.env`.
- The **duplicate-module abort** without `--explicit-package-bases` is itself a project-structure finding (missing/empty `__init__.py` strategy for mypy).

---

## 3. Environment notes (context for reproducing)

- The only `.env` in the repo is `ja-assure-marketing-agent/backend/.env` (keys: `GROQ_API_KEY`, `DATABASE_URL`, `HUNTER_API_KEY`). `ja-assure-submission/backend/` has **no** `.env` — its `Settings()` would crash on import (`GROQ_API_KEY` required).
- The checked-in venv `ja-assure-marketing-agent/venv` is broken on this machine: its `pyvenv.cfg` points to `C:\Users\sharv\...\Python312\python.exe`, which does not exist here. A fresh `.venv` (Python 3.11.9) was created at repo root and used for all checks above.
