import { useState } from 'react'
import { useCustomers } from '@/hooks/use-customers'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Pagination } from '@/components/pagination'
import { formatDate } from '@/lib/utils'

export default function CustomersPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useCustomers({ page: String(page) })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Customers</h1>

      {data?.results?.length ? (
        <>
          <div className="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Stage</TableHead>
                  <TableHead>Deals</TableHead>
                  <TableHead>Synced</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.results.map((c) => (
                  <TableRow key={c.identifier}>
                    <TableCell className="font-medium">{c.full_name}</TableCell>
                    <TableCell>{c.email}</TableCell>
                    <TableCell className="capitalize text-xs text-muted-foreground">{c.lifecycle_stage}</TableCell>
                    <TableCell className="font-mono">{c.deal_count}</TableCell>
                    <TableCell className="text-muted-foreground text-xs">{formatDate(c.synced_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <Pagination page={page} pageSize={25} total={data.count} onPageChange={setPage} />
        </>
      ) : (
        <p className="text-muted-foreground py-12 text-center">{isLoading ? 'Loading...' : 'No customers.'}</p>
      )}
    </div>
  )
}
