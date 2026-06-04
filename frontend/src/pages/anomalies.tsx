import { useState } from 'react'
import { useAnomalies, useResolveAnomaly } from '@/hooks/use-anomalies'
import { AnomalyBadge, SeverityBadge } from '@/components/anomaly-badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog } from '@/components/ui/dialog'
import { formatCurrency, formatDate } from '@/lib/utils'
import type { Anomaly } from '@/types'

export default function AnomaliesPage() {
  const [filters, setFilters] = useState<Record<string, string>>({})
  const { data, isLoading } = useAnomalies(filters)
  const resolveMutation = useResolveAnomaly()
  const [selected, setSelected] = useState<Anomaly | null>(null)
  const [notes, setNotes] = useState('')

  const handleResolve = () => {
    if (!selected) return
    resolveMutation.mutate(
      { id: selected.identifier, data: { resolution_type: 'manual_review', notes } }
    )
    setSelected(null)
    setNotes('')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Anomalies</h1>
        <div className="flex gap-2">
          <select
            className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
            value={filters.anomaly_type ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, anomaly_type: e.target.value }))}
          >
            <option value="">All types</option>
            <option value="missing_payment">Missing Payment</option>
            <option value="amount_mismatch">Amount Mismatch</option>
            <option value="overpayment">Overpayment</option>
            <option value="status_mismatch">Status Mismatch</option>
          </select>
          <select
            className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
            value={filters.severity ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, severity: e.target.value }))}
          >
            <option value="">All severities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      {data?.results?.length ? (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead>Deal</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Expected</TableHead>
                <TableHead>Actual</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.results.map((a) => (
                <TableRow key={a.identifier}>
                  <TableCell><AnomalyBadge anomaly={a} /></TableCell>
                  <TableCell><SeverityBadge severity={a.severity} /></TableCell>
                  <TableCell className="font-mono text-xs max-w-[140px] truncate">{a.deal_name ?? '—'}</TableCell>
                  <TableCell className="text-muted-foreground">{a.customer_email ?? '—'}</TableCell>
                  <TableCell className="font-mono">{a.expected_amount ? formatCurrency(parseFloat(a.expected_amount)) : '—'}</TableCell>
                  <TableCell className="font-mono">{a.actual_amount ? formatCurrency(parseFloat(a.actual_amount)) : '—'}</TableCell>
                  <TableCell>
                    {a.is_resolved ? (
                      <Badge variant="low">Resolved</Badge>
                    ) : (
                      <Badge variant="high">Open</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground text-xs">{formatDate(a.created)}</TableCell>
                  <TableCell>
                    {!a.is_resolved && (
                      <Button size="sm" variant="outline" onClick={() => setSelected(a)}>
                        Resolve
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <p className="text-muted-foreground py-12 text-center">
          {isLoading ? 'Loading...' : 'No anomalies found.'}
        </p>
      )}

      <Dialog open={!!selected} onClose={() => setSelected(null)}>
        <h2 className="text-lg font-semibold mb-4">Resolve Anomaly</h2>
        {selected && (
          <div className="space-y-4">
            <div className="text-sm space-y-1">
              <p><span className="text-muted-foreground">Type:</span> <AnomalyBadge anomaly={selected} /></p>
              <p><span className="text-muted-foreground">Deal:</span> {selected.deal_name ?? '—'}</p>
              <p className="text-muted-foreground">{selected.description}</p>
            </div>
            <textarea
              className="w-full min-h-[80px] rounded-md border border-input bg-transparent px-3 py-2 text-sm resize-y"
              placeholder="Resolution notes..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setSelected(null)}>Cancel</Button>
              <Button onClick={handleResolve} disabled={resolveMutation.isPending}>
                {resolveMutation.isPending ? 'Resolving...' : 'Confirm Resolution'}
              </Button>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  )
}
