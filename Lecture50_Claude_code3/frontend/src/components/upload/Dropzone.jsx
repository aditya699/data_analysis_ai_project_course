import { useRef, useState } from 'react'
import Icon from '../common/Icon'
import { ACCEPT_ATTRIBUTE, MAX_FILE_SIZE_MB } from '../../config/constants'
import './Dropzone.css'

// Drag-and-drop area + hidden file input. Reports raw FileLists upward;
// validation happens in the useFileUpload hook, not here.
export default function Dropzone({ onFilesSelected, hasError }) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef(null)

  function openFilePicker() {
    inputRef.current?.click()
  }

  function handleDrop(e) {
    e.preventDefault()
    setIsDragging(false)
    onFilesSelected(e.dataTransfer.files)
  }

  function handleDragOver(e) {
    e.preventDefault()
    setIsDragging(true)
  }

  function handleDragLeave(e) {
    e.preventDefault()
    setIsDragging(false)
  }

  function handleInputChange(e) {
    onFilesSelected(e.target.files)
    // Reset so picking the same file again still fires onChange
    e.target.value = ''
  }

  const className = [
    'dropzone',
    isDragging && 'dropzone-dragging',
    hasError && 'dropzone-error',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div
      className={className}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={openFilePicker}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          openFilePicker()
        }
      }}
      role="button"
      tabIndex={0}
      aria-label="Upload a CSV or XLSX file"
    >
      <span className="dropzone-icon">
        <Icon name="upload" size={28} />
      </span>
      <p className="dropzone-title">
        {isDragging ? 'Release to upload' : 'Drag & drop your file here'}
      </p>
      <p className="dropzone-hint">
        or <span className="dropzone-link">browse your computer</span>
      </p>
      <div className="dropzone-chips">
        <span className="chip">.csv</span>
        <span className="chip">.xlsx</span>
        <span className="chip">Up to {MAX_FILE_SIZE_MB} MB</span>
        <span className="chip">One file at a time</span>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT_ATTRIBUTE}
        onChange={handleInputChange}
        hidden
      />
    </div>
  )
}
