import type { ReactNode } from 'react';

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: string; actions?: ReactNode }) {
  return <div className="page-header"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h1>{title}</h1>{description && <p>{description}</p>}</div>{actions && <div className="page-actions">{actions}</div>}</div>;
}

export function StatCard({ label, value, note, icon }: { label: string; value: string | number; note?: string; icon?: ReactNode }) {
  return <article className="stat-card"><div className="stat-top"><span>{label}</span>{icon && <div className="stat-icon">{icon}</div>}</div><strong>{value}</strong>{note && <small>{note}</small>}</article>;
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return <div className="empty-state"><div className="empty-orb" /><h3>{title}</h3><p>{description}</p></div>;
}
