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
└── backend/             ← (later) API + analysis agent
```

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
│   ├── constants.js         APP_NAME, file size limit, allowed extensions
│   └── features.js          Content for the feature cards
├── utils/                   Pure JS functions (no React)
│   ├── fileValidation.js    validateFile / validateFileList → error string or null
│   └── formatters.js        formatBytes, formatDate, getFileExtension
├── hooks/                   Custom React hooks (state + behaviour)
│   └── useFileUpload.js     Selected file + error; selectFiles(), clearFile()
├── styles/
│   ├── tokens.css           Colors, radii, shadows, fonts; light + dark mode
│   └── global.css           Reset, body, .container, shared .btn classes
└── components/              One folder per feature area
    ├── common/Icon.jsx      Inline SVG icon set: <Icon name="upload" />
    ├── layout/              Header, Footer
    ├── hero/                Hero (page headline)
    ├── upload/              UploadPanel (container), Dropzone, FileCard,
    │                        UploadError, StepIndicator
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
- Validation runs in the browser (`utils/fileValidation.js`). The backend must
  enforce the same limits again when it is added. Never trust the client alone.
- The "Analyze with agent" button is disabled until the backend exists.

## Backend (`backend/`, to be added)

When the backend is introduced, mirror the same idea of layers:
routes/endpoints → services (analysis, agent) → utils, with config in one place.
Document its structure in this file when it is created.

## Working rules for Claude

- Follow the folder structure above; don't create new top-level folders in
  `src/` without updating this file.
- Run `npm run build` in `frontend/` after changes to confirm it compiles.
- Update this CLAUDE.md whenever the structure or conventions change.
