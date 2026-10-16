// What the agent does with an uploaded file. Shown in FeatureGrid.
// `icon` must be a key in components/common/Icon.jsx.

export const AGENT_FEATURES = [
  {
    icon: 'table',
    title: 'Data profiling',
    description: 'Column types, row counts, distributions and summary stats in seconds.',
  },
  {
    icon: 'shield',
    title: 'Quality checks',
    description: 'Finds missing values, duplicates, outliers and inconsistent formats.',
  },
  {
    icon: 'chart',
    title: 'Auto visualizations',
    description: 'Picks the right charts for your columns and builds them for you.',
  },
  {
    icon: 'bulb',
    title: 'Key insights',
    description: 'Trends, correlations and anomalies explained in plain language.',
  },
  {
    icon: 'chat',
    title: 'Ask your data',
    description: 'Ask questions in plain English and get answers backed by your data.',
  },
  {
    icon: 'report',
    title: 'Shareable report',
    description: 'Export findings and charts as a report you can send to your team.',
  },
]
