import { useState } from 'react'
import { validateFileList } from '../utils/fileValidation'

// Holds the selected file and any validation error.
// Components call selectFiles() with a FileList from drop or <input>.
export function useFileUpload() {
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')

  function selectFiles(fileList) {
    const validationError = validateFileList(fileList)
    if (validationError) {
      setError(validationError)
      return
    }
    setError('')
    setFile(fileList[0])
  }

  function clearFile() {
    setFile(null)
    setError('')
  }

  return { file, error, selectFiles, clearFile }
}
