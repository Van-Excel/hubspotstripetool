import { Badge } from '@/components/ui/badge'
import type { Anomaly } from '@/types'

const config: Record<string, { label: string; variant: 'high' | 'medium' | 'low' }> = {
  missing_payment: { label: 'Missing Payment', variant: 'high' },
  amount_mismatch: { label: 'Amount Mismatch', variant: 'high' },
  overpayment: { label: 'Overpayment', variant: 'medium' },
  status_mismatch: { label: 'Status Mismatch', variant: 'medium' },
}

export function AnomalyBadge({ anomaly }: { anomaly: Anomaly }) {
  const c = config[anomaly.anomaly_type] ?? { label: anomaly.anomaly_type, variant: 'low' as const }
  return <Badge variant={c.variant}>{c.label}</Badge>
}

export function SeverityBadge({ severity }: { severity: Anomaly['severity'] }) {
  const map: Record<string, 'high' | 'medium' | 'low'> = { high: 'high', medium: 'medium', low: 'low' }
  return <Badge variant={map[severity] ?? 'low'}>{severity}</Badge>
}
