import Icon from '../common/Icon'
import { ANALYSIS_TYPE_LABELS, CHART_LABELS } from '../../config/analysis'
import './AnalysisCard.css'

// One suggested analysis from the plan.
export default function AnalysisCard({ item }) {
  const isQuality = item.analysis_type === 'data_quality'

  return (
    <li className="analysis-card">
      <div className="analysis-card-head">
        <span className="analysis-card-rank">{item.priority}</span>
        <h3 className="analysis-card-title">{item.title}</h3>
      </div>
      <p className="analysis-card-question">{item.question}</p>
      <div className="analysis-card-tags">
        <span className={`analysis-tag ${isQuality ? 'analysis-tag-quality' : ''}`}>
          <Icon name={isQuality ? 'shield' : 'chart'} size={13} />
          {ANALYSIS_TYPE_LABELS[item.analysis_type] ?? item.analysis_type}
        </span>
        <span className="analysis-tag">{CHART_LABELS[item.chart] ?? item.chart}</span>
        {item.columns.map((column) => (
          <code key={column} className="analysis-column">
            {column}
          </code>
        ))}
      </div>
      <p className="analysis-card-reason">{item.reason}</p>
    </li>
  )
}
