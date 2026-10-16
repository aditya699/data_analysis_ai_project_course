import Icon from '../common/Icon'
import { AGENT_FEATURES } from '../../config/features'
import './FeatureGrid.css'

export default function FeatureGrid() {
  return (
    <section className="features">
      <h2 className="features-title">What the agent does with your data</h2>
      <div className="features-grid">
        {AGENT_FEATURES.map((feature) => (
          <article key={feature.title} className="feature-card">
            <span className="feature-icon">
              <Icon name={feature.icon} size={20} />
            </span>
            <h3 className="feature-name">{feature.title}</h3>
            <p className="feature-description">{feature.description}</p>
          </article>
        ))}
      </div>
    </section>
  )
}
