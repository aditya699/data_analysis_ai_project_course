import { API_BASE_URL } from '../config/constants'

// Upload flow (see backend CLAUDE.md):
// 1. createUpload  -> backend checks the file details, returns a signed URL
// 2. putFileToStorage -> browser sends the file straight to Azure Blob
// 3. completeUpload -> backend confirms the file arrived

async function postJson(path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.detail ?? `Server error (${response.status}). Try again.`)
  }
  return data
}

export function createUpload(file) {
  return postJson('/api/uploads', {
    filename: file.name,
    size_bytes: file.size,
    content_type: file.type || 'application/octet-stream',
  })
}

// Uses XMLHttpRequest because fetch() can't report upload progress.
// Returns { promise, abort }.
export function putFileToStorage(ticket, file, onProgress) {
  const xhr = new XMLHttpRequest()

  const promise = new Promise((resolve, reject) => {
    xhr.open(ticket.upload_method, ticket.upload_url)
    Object.entries(ticket.upload_headers).forEach(([name, value]) =>
      xhr.setRequestHeader(name, value),
    )
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(Math.round((event.loaded / event.total) * 100))
    }
    xhr.onload = () =>
      xhr.status >= 200 && xhr.status < 300
        ? resolve()
        : reject(new Error(`Storage rejected the file (${xhr.status}). Try again.`))
    xhr.onerror = () =>
      reject(new Error('Could not reach cloud storage. Check your connection and try again.'))
    xhr.onabort = () => reject(new DOMException('Upload cancelled', 'AbortError'))
    xhr.send(file)
  })

  return { promise, abort: () => xhr.abort() }
}

export function completeUpload(uploadId) {
  return postJson(`/api/uploads/${uploadId}/complete`)
}
