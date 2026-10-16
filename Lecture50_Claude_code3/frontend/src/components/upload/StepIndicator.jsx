import Icon from '../common/Icon'
import './StepIndicator.css'

const STEPS = ['Upload data', 'Agent analyzes', 'Get insights']

// currentStep is 0-based: steps before it show as done.
export default function StepIndicator({ currentStep }) {
  return (
    <ol className="steps">
      {STEPS.map((label, index) => {
        const state =
          index < currentStep ? 'done' : index === currentStep ? 'active' : 'upcoming'
        return (
          <li key={label} className={`step step-${state}`}>
            <span className="step-dot">
              {state === 'done' ? <Icon name="check" size={14} strokeWidth={3} /> : index + 1}
            </span>
            <span className="step-label">{label}</span>
          </li>
        )
      })}
    </ol>
  )
}
