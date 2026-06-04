import { useAuditLogs } from '@/hooks/use-audit'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { formatDate } from '@/lib/utils'

export default function AuditPage() {
  const { data, isLoading } = useAuditLogs()

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Audit Log</h1>

      {data?.results?.length ? (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Action</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Details</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.results.map((log) => (
                <TableRow key={log.identifier}>
                  <TableCell className="font-mono text-xs">{log.action}</TableCell>
                  <TableCell className="text-muted-foreground">{log.user_email ?? 'system'}</TableCell>
                  <TableCell className="font-mono text-xs">{log.entity_type}#{log.entity_id}</TableCell>
                  <TableCell className="max-w-[200px] truncate text-xs text-muted-foreground">
                    {log.new_values ? JSON.stringify(log.new_values) : '—'}
                  </TableCell>
                  <TableCell className="text-muted-foreground text-xs">{formatDate(log.created)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <p className="text-muted-foreground py-12 text-center">{isLoading ? 'Loading...' : 'No audit logs.'}</p>
      )}
    </div>
  )
}
