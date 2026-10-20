import { useRef, useState } from 'react'
import { streamPlan } from '../services/analysisApi'

// The analysis plan for one uploaded file, filled in live as the backend streams.
// status: 'idle' | 'loading' | 'ready'
// stages: progress steps received so far, e.g. [{stage: 'reading', message: '...'}]
// items: suggestions shown so far (replaced by the final, re-ranked list on "done")
export function useAnalysisPlan() {
  const [status, setStatus] = useState('idle')
  const [stages, setStages] = useState([])
  const [summary, setSummary] = useState('')
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const abortRef = useRef(null)

  async function generatePlan(uploadId) {
    if (!uploadId || status === 'loading') return
    const controller = new AbortController()
    abortRef.current = controller
    let finished = false

    function handleEvent(name, data) {
      if (name === 'stage') setStages((prev) => [...prev, data])
      else if (name === 'summary') setSummary(data.dataset_summary)
      else if (name === 'item') setItems((prev) => [...prev, data])
      else if (name === 'done') {
        finished = true
        setSummary(data.dataset_summary)
        setItems(data.items)
        setStatus('ready')
      } else if (name === 'error') {
        throw new Error(data.message)
      }
    }

    setError('')
    setStages([])
    setSummary('')
    setItems([])
    setStatus('loading')
    try {
      await streamPlan(uploadId, handleEvent, controller.signal)
      if (!finished) throw new Error('The connection closed before the plan finished. Try again.')
    } catch (err) {
      if (err.name === 'AbortError') return
      setError(err.message)
      setStatus('idle')
    }
  }

  function resetPlan() {
    abortRef.current?.abort()
    abortRef.current = null
    setStatus('idle')
    setStages([])
    setSummary('')
    setItems([])
    setError('')
  }

  return { status, stages, summary, items, error, generatePlan, resetPlan }
}
