export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <div className="brand" aria-label="MEDISCOPE">
      <div className="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 48 48" role="img">
          <path d="M24 5c9 0 16 7 16 16 0 10-8 18-16 22C16 39 8 31 8 21 8 12 15 5 24 5Z" fill="none" stroke="currentColor" strokeWidth="3" />
          <path d="M14 24h7l3-7 4 14 3-7h5" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      {!compact && <div><strong>MEDISCOPE</strong><span>Clinical Intelligence</span></div>}
    </div>
  );
}
