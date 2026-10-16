import Icon from '../common/Icon'
import './Hero.css'

export default function Hero() {
  return (
    <section className="hero">
      <span className="hero-eyebrow">
        <Icon name="sparkles" size={14} strokeWidth={2.2} />
        AI-powered data analysis
      </span>
      <h1 className="hero-title">Drop a spreadsheet. Get answers.</h1>
      <p className="hero-subtitle">
        Upload a CSV or Excel file and the agent profiles your data, flags quality
        issues, builds charts and explains what matters, all in one place.
      </p>
    </section>
  )
}
