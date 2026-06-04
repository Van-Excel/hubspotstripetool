import { useState } from 'react'
import { useDeals } from '@/hooks/use-deals'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { formatCurrency, formatDate } from '@/lib/utils'

export default function DealsPage() {
  const [stage, setStage] = useState('')
  const { data, isLoading } = useDeals(stage ? { stage } : {})

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">Deals</h1>
        <select
          className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
          value={stage}
          onChange={(e) => setStage(e.target.value)}
        >
          <option value="">All stages</option>
          <option value="closedwon">Closed Won</option>
          <option value="closedlost">Closed Lost</option>
          <option value="contractsent">Contract Sent</option>
          <option value="decisionmakerboughtin">Decision Maker</option>
        </select>
      </div>

      {data?.results?.length ? (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Deal</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Stage</TableHead>
                <TableHead>Closed Won</TableHead>
                <TableHead>Synced</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.results.map((d) => (
                <TableRow key={d.identifier}>
                  <TableCell className="font-medium">{d.deal_name}</TableCell>
                  <TableCell className="text-muted-foreground">{d.customer_email}</TableCell>
                  <TableCell className="font-mono">{formatCurrency(parseFloat(d.amount))}</TableCell>
                  <TableCell className="capitalize text-xs">{d.stage}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{formatDate(d.closed_won_at)}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{formatDate(d.synced_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <p className="text-muted-foreground py-12 text-center">{isLoading ? 'Loading...' : 'No deals.'}</p>
      )}
    </div>
  )
}
