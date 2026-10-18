import Icon from '../common/Icon'
import { formatBytes, formatDate, getFileExtension } from '../../utils/formatters'
import './FileCard.css'

const STATUS_LABELS = { idle: 'Ready', uploading: 'Uploading', uploaded: 'Uploaded' }

// Shows the selected file, upload progress and the next action.
export default function FileCard({ file, status, progress, onUpload, onRemove }) {
  const extension = getFileExtension(file.name)
  const isUploading = status === 'uploading'
  const isUploaded = status === 'uploaded'

  return (
    <div className="file-card">
      <div className="file-card-row">
        <span className={`file-badge file-badge-${extension.toLowerCase()}`}>
          <Icon name="file" size={18} />
          {extension}
        </span>
        <div className="file-details">
          <p className="file-name" title={file.name}>
            {file.name}
          </p>
          <p className="file-meta">
            {formatBytes(file.size)} · Modified {formatDate(file.lastModified)}
          </p>
        </div>
        <span className={`file-status file-status-${status}`}>
          {isUploaded && <Icon name="check" size={14} strokeWidth={3} />}
          {STATUS_LABELS[status]}
        </span>
      </div>

      {isUploading && (
        <div
          className="file-progress"
          role="progressbar"
          aria-label="Upload progress"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={progress}
        >
          <div className="file-progress-bar" style={{ width: `${progress}%` }} />
          <span className="file-progress-text">{progress}%</span>
        </div>
      )}

      <div className="file-card-actions">
        <button type="button" className="btn btn-ghost" onClick={onRemove}>
          <Icon name="close" size={16} />
          {isUploading ? 'Cancel' : 'Remove'}
        </button>

        {isUploaded ? (
          // Wired to the backend agent in a later lecture
          <button
            type="button"
            className="btn btn-primary"
            disabled
            title="The analysis engine is connected in an upcoming lecture"
          >
            <Icon name="sparkles" size={16} strokeWidth={2.2} />
            Analyze with agent
          </button>
        ) : (
          <button
            type="button"
            className="btn btn-primary"
            onClick={onUpload}
            disabled={isUploading}
          >
            <Icon name="upload" size={16} strokeWidth={2.2} />
            {isUploading ? `Uploading ${progress}%` : 'Upload file'}
          </button>
        )}
      </div>
      <p className="file-card-note">
        {isUploaded
          ? 'Saved to cloud storage. Analysis engine coming soon.'
          : 'Your file goes straight to secure cloud storage, not through our server.'}
      </p>
    </div>
  )
}
