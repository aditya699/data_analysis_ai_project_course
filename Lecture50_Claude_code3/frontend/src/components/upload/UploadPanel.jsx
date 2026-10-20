import { useFileUpload } from '../../hooks/useFileUpload'
import { useAnalysisPlan } from '../../hooks/useAnalysisPlan'
import StepIndicator from './StepIndicator'
import Dropzone from './Dropzone'
import FileCard from './FileCard'
import UploadError from './UploadError'
import AnalysisPlan from '../analysis/AnalysisPlan'
import Icon from '../common/Icon'
import './UploadPanel.css'

// Container for the whole flow: upload a file, then ask for an analysis plan.
// Owns state via useFileUpload + useAnalysisPlan and passes props down.
export default function UploadPanel() {
  const { file, error, status, progress, upload, selectFiles, clearFile, startUpload } =
    useFileUpload()
  const {
    status: planStatus, stages, summary, items, error: planError, generatePlan, resetPlan,
  } = useAnalysisPlan()

  function handleRemove() {
    resetPlan()
    clearFile()
  }

  const currentStep = planStatus === 'ready' ? 2 : status === 'uploaded' ? 1 : 0

  return (
    <section className="upload-panel" aria-label="Upload data">
      <StepIndicator currentStep={currentStep} />

      {file ? (
        <FileCard
          file={file}
          status={status}
          progress={progress}
          planStatus={planStatus}
          onUpload={startUpload}
          onPlan={() => generatePlan(upload?.upload_id)}
          onRemove={handleRemove}
        />
      ) : (
        <Dropzone onFilesSelected={selectFiles} hasError={Boolean(error)} />
      )}

      <UploadError message={error || planError} />

      {planStatus !== 'idle' && (
        <AnalysisPlan
          stages={stages}
          summary={summary}
          items={items}
          isLoading={planStatus === 'loading'}
        />
      )}

      <p className="upload-privacy">
        <Icon name="lock" size={14} />
        Files are sent over HTTPS to private cloud storage. The agent sees column
        summaries and a few sample rows, not your whole file.
      </p>
    </section>
  )
}
