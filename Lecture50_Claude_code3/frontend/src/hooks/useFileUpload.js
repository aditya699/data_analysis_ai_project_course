import { useRef, useState } from 'react'
import { validateFileList } from '../utils/fileValidation'
import { completeUpload, createUpload, putFileToStorage } from '../services/uploadApi'

// Holds the selected file, validation/upload errors and upload progress.
// status: 'idle' (selected, not sent) | 'uploading' | 'uploaded'
export function useFileUpload() {
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('idle')
  const [progress, setProgress] = useState(0)
  const [upload, setUpload] = useState(null)
  const abortRef = useRef(null)

  function reset() {
    abortRef.current?.()
    abortRef.current = null
    setStatus('idle')
    setProgress(0)
    setUpload(null)
  }

  function selectFiles(fileList) {
    const validationError = validateFileList(fileList)
    if (validationError) {
      setError(validationError)
      return
    }
    reset()
    setError('')
    setFile(fileList[0])
  }

  function clearFile() {
    reset()
    setFile(null)
    setError('')
  }

  async function startUpload() {
    if (!file || status === 'uploading') return
    setError('')
    setProgress(0)
    setStatus('uploading')
    try {
      const ticket = await createUpload(file)
      const { promise, abort } = putFileToStorage(ticket, file, setProgress)
      abortRef.current = abort
      await promise
      abortRef.current = null
      setUpload(await completeUpload(ticket.upload_id))
      setStatus('uploaded')
    } catch (err) {
      if (err.name === 'AbortError') return
      setError(err.message)
      setStatus('idle')
    }
  }

  return { file, error, status, progress, upload, selectFiles, clearFile, startUpload }
}
