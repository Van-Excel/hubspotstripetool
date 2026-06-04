import { useState } from 'react'
import { useAuditLogs } from '@/hooks/use-audit'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { formatDate } from '@/lib/utils'
import type { AuditLog } from '@/types'
import { X } from 'lucide-react'

export default function AuditPage() {
  const { data, isLoading } = useAuditLogs()
  const [selected, setSelected] = useState<AuditLog | null>(null)

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
                <TableRow
                  key={log.identifier}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => setSelected(log)}
                >
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

      <Dialog open={!!selected} onClose={() => setSelected(null)}>
        {selected && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="low">{selected.action}</Badge>
                <span className="text-sm text-muted-foreground">
                  {formatDate(selected.created)}
                </span>
              </div>
              <button onClick={() => setSelected(null)} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">User</span>
                <p className="font-medium">{selected.user_email ?? 'System'}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Entity</span>
                <p className="font-mono text-xs">{selected.entity_type} #{selected.entity_id}</p>
              </div>
            </div>

            {selected.old_values && Object.keys(selected.old_values).length > 0 && (
              <div>
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Before</span>
                <pre className="mt-1 rounded-md bg-muted p-3 text-xs font-mono overflow-auto max-h-32">
                  {JSON.stringify(selected.old_values, null, 2)}
                </pre>
              </div>
            )}

            {selected.new_values && Object.keys(selected.new_values).length > 0 && (
              <div>
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">After</span>
                <pre className="mt-1 rounded-md bg-muted p-3 text-xs font-mono overflow-auto max-h-32">
                  {JSON.stringify(selected.new_values, null, 2)}
                </pre>
              </div>
            )}

            {selected.ip_address && (
              <div className="text-xs text-muted-foreground">
                IP: {selected.ip_address}
              </div>
            )}
          </div>
        )}
      </Dialog>
    </div>
  )
}
