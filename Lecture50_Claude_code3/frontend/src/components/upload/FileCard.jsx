import Icon from '../common/Icon'
import { formatBytes, formatDate, getFileExtension } from '../../utils/formatters'
import './FileCard.css'

// Shows the accepted file with Remove and Analyze actions.
export default function FileCard({ file, onRemove }) {
  const extension = getFileExtension(file.name)

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
        <span className="file-status">
          <Icon name="check" size={14} strokeWidth={3} />
          Ready
        </span>
      </div>

      <div className="file-card-actions">
        <button type="button" className="btn btn-ghost" onClick={onRemove}>
          <Icon name="close" size={16} />
          Remove
        </button>
        {/* Wired to the backend agent in a later lecture */}
        <button
          type="button"
          className="btn btn-primary"
          disabled
          title="The analysis engine is connected in an upcoming lecture"
        >
          <Icon name="sparkles" size={16} strokeWidth={2.2} />
          Analyze with agent
        </button>
      </div>
      <p className="file-card-note">
        Analysis engine coming soon. Your file stays in this browser for now.
      </p>
    </div>
  )
}
