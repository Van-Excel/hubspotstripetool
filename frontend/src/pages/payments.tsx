import { useState } from 'react'
import { usePayments } from '@/hooks/use-payments'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { formatCurrency, formatDate } from '@/lib/utils'

const statusColor: Record<string, 'high' | 'low' | 'medium'> = {
  succeeded: 'low',
  failed: 'high',
  pending: 'medium',
  processing: 'medium',
  refunded: 'medium',
}

export default function PaymentsPage() {
  const [statusFilter, setStatusFilter] = useState('')
  const { data, isLoading } = usePayments(statusFilter ? { status: statusFilter } : {})

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Payments</h1>
        <select
          className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All statuses</option>
          <option value="succeeded">Succeeded</option>
          <option value="failed">Failed</option>
          <option value="pending">Pending</option>
          <option value="processing">Processing</option>
        </select>
      </div>

      {data?.results?.length ? (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Stripe ID</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Currency</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Provider</TableHead>
                <TableHead>Synced</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.results.map((p) => (
                <TableRow key={p.identifier}>
                  <TableCell className="font-mono text-xs">{p.stripe_payment_intent_id ?? '—'}</TableCell>
                  <TableCell>{p.customer_email}</TableCell>
                  <TableCell className="font-mono">{formatCurrency(parseFloat(p.amount))}</TableCell>
                  <TableCell className="uppercase text-xs text-muted-foreground">{p.currency}</TableCell>
                  <TableCell>
                    <Badge variant={statusColor[p.status] ?? 'low'}>{p.status}</Badge>
                  </TableCell>
                  <TableCell className="capitalize text-muted-foreground">{p.provider}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{formatDate(p.synced_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <p className="text-muted-foreground py-12 text-center">{isLoading ? 'Loading...' : 'No payments.'}</p>
      )}
    </div>
  )
}
