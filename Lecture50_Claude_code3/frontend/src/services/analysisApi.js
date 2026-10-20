import { API_BASE_URL } from '../config/constants'

// Streams the analysis plan as Server-Sent Events.
// onEvent(name, data) is called for each event, in order:
//   stage* -> summary -> item* -> done   (or error)
// EventSource only supports GET, so we read the POST response body ourselves.
export async function streamPlan(uploadId, onEvent, signal) {
  const response = await fetch(`${API_BASE_URL}/api/uploads/${uploadId}/plan/stream`, {
    method: 'POST',
    signal,
  })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(data.detail ?? `Could not create the plan (${response.status}). Try again.`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // Events are separated by a blank line; keep any half-received event in the buffer.
    const parts = buffer.split('\n\n')
    buffer = parts.pop()
    for (const part of parts) {
      const event = parseEvent(part)
      if (event) onEvent(event.name, event.data)
    }
  }
}

function parseEvent(block) {
  let name = 'message'
  let data = ''
  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) name = line.slice(6).trim()
    else if (line.startsWith('data:')) data += line.slice(5).trim()
  }
  return data ? { name, data: JSON.parse(data) } : null
}
