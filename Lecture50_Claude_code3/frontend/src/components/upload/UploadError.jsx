import Icon from '../common/Icon'
import './UploadError.css'

export default function UploadError({ message }) {
  if (!message) return null

  return (
    <div className="upload-error" role="alert">
      <Icon name="alert" size={18} />
      <span>{message}</span>
    </div>
  )
}
