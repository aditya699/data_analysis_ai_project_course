import AnalysisCard from './AnalysisCard'
import PlanProgress from './PlanProgress'
import './AnalysisPlan.css'

// Suggested analyses, drawn live: progress first, then each card as it arrives.
export default function AnalysisPlan({ stages, summary, items, isLoading }) {
  return (
    <section className="analysis-plan" aria-label="Suggested analyses" aria-busy={isLoading}>
      <div className="analysis-plan-head">
        <h2 className="analysis-plan-title">Suggested analyses</h2>
        {summary && <p className="analysis-plan-summary">{summary}</p>}
      </div>

      <PlanProgress stages={stages} isLoading={isLoading} />

      <ol className="analysis-plan-list">
        {items.map((item) => (
          <AnalysisCard key={`${item.priority}-${item.title}`} item={item} />
        ))}
        {isLoading && <li className="analysis-plan-skeleton" aria-hidden="true" />}
      </ol>
    </section>
  )
}
