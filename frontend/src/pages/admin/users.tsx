import { useUsers, useUpdateUser } from '@/hooks/use-users'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatDate } from '@/lib/utils'

export default function AdminUsersPage() {
  const { data, isLoading } = useUsers()
  const updateUser = useUpdateUser()

  const handleRoleChange = (userId: string, role: string) => {
    updateUser.mutate({ id: userId, data: { role } })
  }

  const toggleActive = (userId: string, isActive: boolean) => {
    updateUser.mutate({ id: userId, data: { is_active: !isActive } })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">User Management</h1>

      {data?.results?.length ? (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Joined</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.results.map((u) => (
                <TableRow key={u.identifier}>
                  <TableCell className="font-medium">{u.full_name}</TableCell>
                  <TableCell>{u.email}</TableCell>
                  <TableCell>
                    <Badge variant="low">{u.account?.role?.name ?? '—'}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={u.is_active ? 'low' : 'high'}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground text-xs">{formatDate(u.date_joined)}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <select
                        className="h-7 rounded border border-input bg-transparent px-2 text-xs"
                        value={u.account?.role?.name ?? 'viewer'}
                        onChange={(e) => handleRoleChange(u.identifier, e.target.value)}
                      >
                        <option value="admin">Admin</option>
                        <option value="analyst">Analyst</option>
                        <option value="viewer">Viewer</option>
                      </select>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => toggleActive(u.identifier, u.is_active)}
                      >
                        {u.is_active ? 'Deactivate' : 'Activate'}
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <p className="text-muted-foreground py-12 text-center">{isLoading ? 'Loading...' : 'No users.'}</p>
      )}
    </div>
  )
}
