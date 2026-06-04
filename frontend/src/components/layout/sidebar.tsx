import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  AlertTriangle,
  CreditCard,
  Handshake,
  Users,
  ShieldCheck,
  Settings,
} from 'lucide-react'

const links = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, perm: null },
  { to: '/anomalies', label: 'Anomalies', icon: AlertTriangle, perm: null },
  { to: '/payments', label: 'Payments', icon: CreditCard, perm: null },
  { to: '/deals', label: 'Deals', icon: Handshake, perm: null },
  { to: '/customers', label: 'Customers', icon: Users, perm: null },
  { to: '/audit', label: 'Audit Log', icon: ShieldCheck, perm: null },
]

const adminLinks = [
  { to: '/admin/users', label: 'Users', icon: Settings, perm: null },
]

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-56 border-r bg-[#00305a] text-white flex flex-col">
      <div className="flex h-14 items-center gap-2 border-b border-white/10 px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded bg-white/10 text-sm font-bold">
          ICC
        </div>
        <div className="flex flex-col">
          <span className="text-xs font-semibold tracking-tight leading-tight">Commerce</span>
          <span className="text-[10px] text-white/60 leading-tight">Monitor</span>
        </div>
      </div>
      <nav className="flex-1 space-y-0.5 p-2">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-white/15 text-white'
                  : 'text-white/60 hover:bg-white/10 hover:text-white'
              )
            }
          >
            <link.icon className="h-4 w-4" />
            {link.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-white/10 p-2">
        {adminLinks.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-white/15 text-white'
                  : 'text-white/60 hover:bg-white/10 hover:text-white'
              )
            }
          >
            <link.icon className="h-4 w-4" />
            {link.label}
          </NavLink>
        ))}
      </div>
    </aside>
  )
}
