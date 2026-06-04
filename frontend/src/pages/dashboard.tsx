import { useDashboard } from '@/hooks/use-dashboard'
import { StatCard } from '@/components/stat-card'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useAnomalies } from '@/hooks/use-anomalies'
import { AnomalyBadge, SeverityBadge } from '@/components/anomaly-badge'
import { formatCurrency, formatDate } from '@/lib/utils'
import { useNavigate } from 'react-router-dom'

export default function DashboardPage() {
  const { data: stats, isLoading } = useDashboard()
  const { data: anomalies } = useAnomalies({})
  const navigate = useNavigate()

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32 rounded-lg" />)
        ) : (
          <>
            <StatCard
              title="High Severity"
              value={stats?.by_severity?.high ?? 0}
              subtitle="Requires attention"
              variant="red"
            />
            <StatCard
              title="Medium Severity"
              value={stats?.by_severity?.medium ?? 0}
              subtitle="Under review"
              variant="amber"
            />
            <StatCard
              title="Low Severity"
              value={stats?.by_severity?.low ?? 0}
              subtitle="Minor issues"
            />
            <StatCard
              title="Resolved"
              value={stats?.resolved_anomalies ?? 0}
              subtitle={`Out of ${stats?.total_anomalies ?? 0} total`}
              variant="muted"
            />
          </>
        )}
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Anomalies</CardTitle>
          <span
            className="text-sm text-primary cursor-pointer hover:underline"
            onClick={() => navigate('/anomalies')}
          >
            View all
          </span>
        </CardHeader>
        <CardContent>
          {anomalies?.results?.length ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Deal</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Expected</TableHead>
                  <TableHead>Actual</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {anomalies.results.slice(0, 10).map((a) => (
                  <TableRow key={a.identifier}>
                    <TableCell><AnomalyBadge anomaly={a} /></TableCell>
                    <TableCell><SeverityBadge severity={a.severity} /></TableCell>
                    <TableCell className="font-mono text-xs">{a.deal_name ?? '—'}</TableCell>
                    <TableCell className="text-muted-foreground">{a.customer_email ?? '—'}</TableCell>
                    <TableCell className="font-mono">{a.expected_amount ? formatCurrency(parseFloat(a.expected_amount)) : '—'}</TableCell>
                    <TableCell className="font-mono">{a.actual_amount ? formatCurrency(parseFloat(a.actual_amount)) : '—'}</TableCell>
                    <TableCell className="text-muted-foreground">{formatDate(a.created)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-muted-foreground py-8 text-center">No anomalies found.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
