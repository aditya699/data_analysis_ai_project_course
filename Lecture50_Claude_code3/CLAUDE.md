# Auto Data Analyst Agent

An AI agent where users upload one CSV or XLSX file (max 100 MB) and get back
data profiling, quality checks, charts, insights and plain-English Q&A.

This project is built step by step during the course. Follow the structure and
conventions below in every lecture so the codebase stays modular.

## Project layout

```
Lecture50_Claude_code3/
├── CLAUDE.md            ← this file (project rules)
├── frontend/            ← React + Vite app (the UI)
├── sample_data/         ← test datasets + the scripts that generate them
└── backend/             ← FastAPI: uploads to Azure Blob (later: analysis agent)
```

## Sample data (`sample_data/`)

Synthetic datasets for testing uploads and, later, the agent's analysis.
Every dataset is produced by a script so it can be regenerated.

- `generate_upi_data.py`: standard library only, fixed seed (reproducible).
  Run `python generate_upi_data.py [rows]` (default 5,000) to write
  `upi_transactions.csv` and `upi_transactions.xlsx`.
- The UPI data includes deliberate quality issues: missing city/state and
  UPI app, inconsistent `merchant_category` casing/spacing, a few extreme
  amounts (up to ₹2.5 lakh) and ~20 exact duplicate rows. Keep these, since
  they are what the agent's quality checks should detect.
- All names, VPAs and IDs are fictional. Never put real personal or
  financial data in this folder.
- New datasets: add a `generate_<name>.py` script next to the output files.

## Frontend (`frontend/`)

Stack: React 18, Vite 6, plain CSS with design tokens. No UI library.

Run it:

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build    # production build into dist/
```

### Folder structure

```
frontend/src/
├── main.jsx                 Entry point: mounts <App/>, imports global styles
├── App.jsx                  Composes page sections only. No state, no logic.
├── config/                  Constants and static content
│   ├── constants.js         APP_NAME, file size limit, allowed extensions, API_BASE_URL
│   ├── features.js          Content for the feature cards
│   └── analysis.js          Display labels for analysis types and chart types
├── utils/                   Pure JS functions (no React)
│   ├── fileValidation.js    validateFile / validateFileList → error string or null
│   └── formatters.js        formatBytes, formatDate, getFileExtension
├── services/                Backend calls (no React)
│   ├── uploadApi.js         createUpload, putFileToStorage (XHR + progress), completeUpload
│   └── analysisApi.js       streamPlan(uploadId, onEvent, signal): reads the SSE stream
├── hooks/                   Custom React hooks (state + behaviour)
│   ├── useFileUpload.js     File, error, status (idle|uploading|uploaded), progress;
│   │                        selectFiles(), clearFile(), startUpload()
│   └── useAnalysisPlan.js   status (idle|loading|ready), stages, summary, items, error;
│                            generatePlan(), resetPlan() (aborts a running stream)
├── styles/
│   ├── tokens.css           Colors, radii, shadows, fonts; light + dark mode
│   └── global.css           Reset, body, .container, shared .btn classes
└── components/              One folder per feature area
    ├── common/Icon.jsx      Inline SVG icon set: <Icon name="upload" />
    ├── layout/              Header, Footer
    ├── hero/                Hero (page headline)
    ├── upload/              UploadPanel (container for upload + plan), Dropzone,
    │                        FileCard, UploadError, StepIndicator
    ├── analysis/            AnalysisPlan (list + skeleton), AnalysisCard (one suggestion),
    │                        PlanProgress (live stage checklist)
    └── features/            FeatureGrid
```

### Where new code goes

| You are adding…                          | Put it in                                  |
|------------------------------------------|--------------------------------------------|
| A limit, label, URL or other constant    | `config/constants.js`                      |
| Static content (lists of cards, copy)    | `config/<name>.js`                         |
| A pure helper (parsing, formatting)      | `utils/<name>.js`                          |
| State or side effects (fetching, upload) | `hooks/use<Name>.js`                       |
| Calls to the backend API                 | `services/<name>Api.js` (create when needed) |
| A new UI piece                           | `components/<area>/<Name>.jsx` + `<Name>.css` |
| A new color or spacing value             | `styles/tokens.css`                        |

### Conventions

- **Layers flow one way:** `components → hooks → utils/services → config`.
  Utils never import React; components never contain validation or API logic.
- **Container vs presentational:** one container per feature (e.g.
  `UploadPanel`) calls the hook and passes data/callbacks down as props.
  Child components (`Dropzone`, `FileCard`) only render props and raise events.
- **One component per file**, PascalCase file name, default export.
  Hooks and utils use camelCase file names and named exports.
- **Colocated CSS:** each component imports its own `Name.css`. Prefix class
  names with the component name (`.file-card`, `.file-card-actions`) to avoid
  clashes. Shared classes (`.btn`, `.container`) live in `global.css`.
- **Colors only via tokens:** use `var(--brand)`, `var(--text-muted)`, etc.
  Never hard-code hex values in component CSS (dark mode depends on this).
  New tokens must be defined for both light and dark in `tokens.css`.
- **Icons:** add new paths to `components/common/Icon.jsx`; don't add an icon library.
- **No magic numbers in components:** limits like `MAX_FILE_SIZE_MB` come from `config/`.
- **Accessibility:** interactive non-button elements need `role`, `tabIndex`
  and keyboard handlers; errors use `role="alert"`.
- Keep `App.jsx` as a list of sections. If it starts holding state, move
  that state into a hook or a container component.

### Upload rules (current behaviour)

- Only `.csv` and `.xlsx`; one file at a time; max 100 MB; empty files rejected.
- Validation runs in the browser (`utils/fileValidation.js`); the backend
  enforces the same limits again. Never trust the client alone.
- "Upload file" runs the 3-step backend flow and PUTs the file straight to
  Azure Blob with a progress bar. Remove during upload cancels it.
- After upload, "Suggest analyses" opens the plan stream: a live checklist of
  stages, then each card appears as Claude finishes writing it, with a
  skeleton card for the next one. Removing the file aborts and clears the plan.
- API URL: `VITE_API_URL` in `frontend/.env.local` (git-ignored), default
  `http://127.0.0.1:8000`. On this machine port 8000 is taken, so it is `8010`.

## Backend (`backend/`)

Stack: Python 3.13, FastAPI, pydantic-settings, azure-storage-blob, SQLite,
pandas, Anthropic SDK (Claude, model in `LLM_MODEL`, default `claude-opus-5-5`).
Files are stored in the Azure Blob container **`course-files`**.

Run it (put the storage connection string in `backend/.env`, see `.env.example`):

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload      # http://127.0.0.1:8000/docs
```

### Upload flow (direct-to-blob with a signed URL)

The API never receives the file bytes. It hands out a short-lived SAS URL and
the browser PUTs the file straight to Azure.

1. `POST /api/uploads` `{filename, size_bytes, content_type}` → re-validates
   (.csv/.xlsx, ≤ 100 MB, not empty), returns `upload_id`, `upload_url`
   (write-only SAS, 10 min) and `upload_headers` (incl. `x-ms-blob-type: BlockBlob`).
2. Client `PUT`s the file to `upload_url` with those headers.
3. `POST /api/uploads/{id}/complete` → checks the blob exists and its size
   matches; if not, deletes it and marks the upload `failed`.
4. `GET /api/uploads/{id}` → upload record (status `pending | uploaded | failed`).

Blob key: `uploads/{upload_id}/original.<ext>` inside `course-files`. Never
use the user's file name as the key; it is kept only as metadata in SQLite.

### Plan feature (current scope)

We build the AI pipeline one step at a time. Only **Plan** exists: Claude
suggests which analyses to run. Nothing is computed or charted yet.

`POST /api/uploads/{id}/plan` (synchronous, a few seconds):
1. Download the blob and load it with pandas (whole file; no scaling yet).
2. `profiler.py` builds a profile: per column a semantic type decided in code
   (`numeric | datetime | categorical | id | text`), null %, unique count,
   stats or top values, plus a few sample rows. The LLM sees only this.
3. Prompt = `prompts/analysis_plan_v1.md` (system) + profile JSON in
   `<dataset_profile>` tags (user).
4. `llm_client.py` calls `messages.parse(output_format=AnalysisPlan)` so the
   reply is always a validated Pydantic object (structured output).
5. `analysis_planner.py` drops items that use unknown columns, re-ranks by
   priority, keeps at most `PLAN_MAX_ITEMS`.
6. Saves `reports/{id}/profile.json` and `reports/{id}/plan.json` to blob.

`GET /api/uploads/{id}/plan` returns the saved plan. Errors: 400 bad/unfinished
upload, 404 unknown upload or no plan yet, 502 LLM failure (`LLMError`).

**Streaming (what the UI uses):** `POST /api/uploads/{id}/plan/stream` returns
Server-Sent Events, in order:
`stage` (reading → profiling → thinking → writing) → `summary` → `item` (one
per suggestion, as soon as its JSON object closes) → `done` (the full, final
plan, same shape as `POST /plan`) or `error` (`{message}`).
- `llm_client.stream_parse()` uses `messages.stream(..., output_format=...)`
  and yields `thinking` / `text` / `final` events.
- `utils/plan_stream_parser.py` scans the partial JSON and pulls out the
  summary and each finished item. Streamed items are validated and checked
  against real columns; `done` carries the re-ranked final list, which the UI
  swaps in.
- Pre-checks (404/400) run before the stream starts; after that the status
  is already 200, so failures arrive as an `error` event.
- `POST /plan` (non-streaming) reuses the same generator and waits for `done`.
- Measured on the 5,020-row UPI CSV: first event 0.8 s, profiling ~9 s,
  cards from ~19 s, done ~30 s.

Prompts are versioned files. To change the prompt, add `analysis_plan_v2.md`
and switch `SYSTEM_PROMPT` in `analysis_planner.py`; don't edit a version in place.

### Folder structure

```
backend/
├── requirements.txt
├── .env.example             Copy to .env (git-ignored) and fill in
├── data/uploads.db          SQLite upload records (git-ignored, auto-created)
└── app/
    ├── main.py              FastAPI app, CORS, startup (ensure container)
    ├── config.py            Settings from .env + upload limits (same as frontend)
    ├── dependencies.py      Builds shared services once for Depends()
    ├── schemas.py           Pydantic request/response models
    ├── prompts/
    │   └── analysis_plan_v1.md  System prompt for the planner
    ├── routes/              HTTP only: parse request, call service, map errors
    │   ├── health.py        GET /api/health
    │   ├── uploads.py       The three upload endpoints
    │   └── analysis.py      POST /plan/stream (SSE), POST/GET /api/uploads/{id}/plan
    ├── services/
    │   ├── blob_storage.py      All Azure calls: SAS URL, size, download, upload, CORS
    │   ├── upload_registry.py   SQLite CRUD for upload records
    │   ├── upload_service.py    Upload flow: validate → sign → verify
    │   ├── profiler.py          pandas: file → profile dict (no LLM)
    │   ├── llm_client.py        Only file that imports anthropic (streaming structured output)
    │   └── analysis_planner.py  Plan flow: profile → prompt → Claude → validate → save
    └── utils/
        ├── file_rules.py          Pure helpers: extension, validation, blob name
        └── plan_stream_parser.py  Pulls summary/items out of partial streamed JSON
```

### Conventions

- **Layers flow one way:** `routes → services → utils`, all reading `config`.
  Routes contain no business logic; only `blob_storage.py` imports Azure and
  only `llm_client.py` imports the Anthropic SDK.
- Services raise `UploadError` (→ 400) / `UploadNotFound` (→ 404); routes map
  them to `HTTPException`.
- Limits live in `config.py` and must match `frontend/src/config/constants.js`.
- Secrets only in `backend/.env` (`BLOB_STORAGE_CONNECTION_STRING`,
  `ANTHROPIC_API_KEY`); never commit it or print them.
- The browser can only PUT to Azure if the storage account's CORS allows the
  frontend origin. With `CONFIGURE_STORAGE_CORS=true` (default) the API adds a
  rule for `CORS_ORIGINS` on startup. It never removes existing rules: the
  account also serves other sites. CORS is per account, not per container.
- Local dev here: `py -3.13 -m uvicorn app.main:app --port 8010 --reload`
  (`python` on PATH is the Azure CLI's bundled Python; port 8000 is in use).

## Working rules for Claude

- Follow the folder structure above; don't create new top-level folders in
  `src/` without updating this file.
- Run `npm run build` in `frontend/` after changes to confirm it compiles.
- Update this CLAUDE.md whenever the structure or conventions change.
