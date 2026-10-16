import Icon from '../common/Icon'
import { APP_NAME } from '../../config/constants'
import './Header.css'

export default function Header() {
  return (
    <header className="header">
      <div className="container header-inner">
        <div className="brand">
          <span className="brand-mark">
            <Icon name="logo" size={18} strokeWidth={2.4} />
          </span>
          <span className="brand-name">{APP_NAME}</span>
          <span className="brand-tag">Beta</span>
        </div>
      </div>
    </header>
  )
}
