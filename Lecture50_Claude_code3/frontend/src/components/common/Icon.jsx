// Small inline SVG icon set (stroke icons, 24x24 grid).
// Usage: <Icon name="upload" size={20} />

const PATHS = {
  logo: 'M4 19V9m5 10V5m5 14v-7m5 7V3',
  upload: 'M12 16V4m0 0-5 5m5-5 5 5M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3',
  file: 'M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8l-5-5Zm0 0v5h5',
  alert: 'M12 8v5m0 3h.01M10.3 3.9 2.6 17.5A2 2 0 0 0 4.3 20.5h15.4a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z',
  check: 'M5 12.5 10 17 19 7',
  close: 'M6 6l12 12M18 6 6 18',
  sparkles: 'M12 3v4m0 10v4M3 12h4m10 0h4M6 6l2 2m8 8 2 2M6 18l2-2m8-8 2-2',
  table: 'M3 5h18v14H3zM3 10h18M3 15h18M9 5v14',
  shield: 'M12 3 4 6v6c0 4.5 3.4 8 8 9 4.6-1 8-4.5 8-9V6l-8-3Z',
  chart: 'M4 20V10m6 10V4m6 16v-7m4 7H2',
  bulb: 'M9 18h6m-5 3h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2V16h5v-.1c0-.8.4-1.5 1-2A6 6 0 0 0 12 3Z',
  chat: 'M4 5h16v11H8l-4 4V5Z',
  report: 'M8 3h8l4 4v14H4V3h4Zm0 9h8m-8 4h5',
  lock: 'M6 11h12v10H6zM8 11V7a4 4 0 0 1 8 0v4',
}

export default function Icon({ name, size = 20, strokeWidth = 1.8, className }) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={PATHS[name]} />
    </svg>
  )
}
