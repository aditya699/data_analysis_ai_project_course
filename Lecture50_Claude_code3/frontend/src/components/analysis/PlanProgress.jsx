import Icon from '../common/Icon'
import './PlanProgress.css'

// Live checklist of what the backend is doing. Every stage before the last
// is done; the last one is still running while isLoading is true.
export default function PlanProgress({ stages, isLoading }) {
  if (stages.length === 0 && !isLoading) return null
  const shown = stages.length ? stages : [{ stage: 'starting', message: 'Starting…' }]

  return (
    <ol className="plan-progress" aria-live="polite">
      {shown.map((step, index) => {
        const running = isLoading && index === shown.length - 1
        return (
          <li key={step.stage} className={`plan-progress-step ${running ? 'is-running' : ''}`}>
            {running ? (
              <span className="plan-progress-spinner" aria-hidden="true" />
            ) : (
              <Icon name="check" size={14} strokeWidth={3} />
            )}
            {step.message}
          </li>
        )
      })}
    </ol>
  )
}
