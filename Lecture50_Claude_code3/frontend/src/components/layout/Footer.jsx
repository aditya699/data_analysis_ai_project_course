import { APP_NAME } from '../../config/constants'
import './Footer.css'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        {APP_NAME} · Built during the Data Analysis AI Project course
      </div>
    </footer>
  )
}
