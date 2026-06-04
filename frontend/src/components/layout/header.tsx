import { useAuth } from '@/providers/auth-provider'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { LogOut } from 'lucide-react'

export function Header() {
  const { user, logout } = useAuth()
  const initials = user
    ? `${user.first_name?.[0] ?? ''}${user.last_name?.[0] ?? ''}`.toUpperCase()
    : '?'

  return (
    <header className="flex h-14 items-center justify-between border-b px-6">
      <span className="text-sm text-muted-foreground">
        {user?.account?.role?.name && (
          <span className="capitalize font-medium text-foreground">{user.account.role.name}</span>
        )}
      </span>
      <div className="flex items-center gap-3">
        <Avatar>
          <AvatarFallback className="text-xs bg-primary text-primary-foreground">{initials}</AvatarFallback>
        </Avatar>
        <span className="text-sm font-medium">{user?.full_name ?? user?.email}</span>
        <Button variant="ghost" size="sm" onClick={logout}>
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}
