// App-wide constants. Change limits and copy here, not inside components.

export const APP_NAME = 'Auto Data Analyst Agent'

export const MAX_FILE_SIZE_MB = 100
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

export const ALLOWED_EXTENSIONS = ['.csv', '.xlsx']

// Value for the <input accept="..."> attribute
export const ACCEPT_ATTRIBUTE = [
  ...ALLOWED_EXTENSIONS,
  'text/csv',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
].join(',')

// Backend API. Override per machine in frontend/.env.local, e.g.
// VITE_API_URL=http://127.0.0.1:8010
export const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'
