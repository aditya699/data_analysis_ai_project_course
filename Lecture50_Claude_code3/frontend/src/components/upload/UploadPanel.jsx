import { useFileUpload } from '../../hooks/useFileUpload'
import StepIndicator from './StepIndicator'
import Dropzone from './Dropzone'
import FileCard from './FileCard'
import UploadError from './UploadError'
import Icon from '../common/Icon'
import './UploadPanel.css'

// Container for the upload flow: owns state via useFileUpload and
// decides which child (Dropzone or FileCard) to show.
export default function UploadPanel() {
  const { file, error, status, progress, selectFiles, clearFile, startUpload } = useFileUpload()

  return (
    <section className="upload-panel" aria-label="Upload data">
      <StepIndicator currentStep={status === 'uploaded' ? 1 : 0} />

      {file ? (
        <FileCard
          file={file}
          status={status}
          progress={progress}
          onUpload={startUpload}
          onRemove={clearFile}
        />
      ) : (
        <Dropzone onFilesSelected={selectFiles} hasError={Boolean(error)} />
      )}

      <UploadError message={error} />

      <p className="upload-privacy">
        <Icon name="lock" size={14} />
        Files are checked in your browser, then sent over HTTPS to private cloud storage.
      </p>
    </section>
  )
}
