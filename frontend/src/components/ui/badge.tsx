import { cn } from '@/lib/utils'

const variants = {
  high: 'bg-red-50 text-red-700 border border-red-200',
  medium: 'bg-amber-50 text-amber-700 border border-amber-200',
  low: 'bg-slate-50 text-slate-600 border border-slate-200',
}

export function Badge({
  className,
  variant = 'low',
  children,
}: {
  className?: string
  variant?: keyof typeof variants
  children: React.ReactNode
}) {
  return (
    <span className={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium', variants[variant], className)}>
      {children}
    </span>
  )
}
