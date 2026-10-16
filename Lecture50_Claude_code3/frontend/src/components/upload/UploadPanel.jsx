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
  const { file, error, selectFiles, clearFile } = useFileUpload()

  return (
    <section className="upload-panel" aria-label="Upload data">
      <StepIndicator currentStep={file ? 1 : 0} />

      {file ? (
        <FileCard file={file} onRemove={clearFile} />
      ) : (
        <Dropzone onFilesSelected={selectFiles} hasError={Boolean(error)} />
      )}

      <UploadError message={error} />

      <p className="upload-privacy">
        <Icon name="lock" size={14} />
        Files are checked in your browser. Nothing is uploaded until you start an analysis.
      </p>
    </section>
  )
}
