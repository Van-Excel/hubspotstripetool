import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

export function StatCard({
  title,
  value,
  subtitle,
  variant = 'default',
}: {
  title: string
  value: string | number
  subtitle?: string
  variant?: 'red' | 'amber' | 'muted' | 'default'
}) {
  const bgMap = {
    red: 'bg-red-50 border-red-200',
    amber: 'bg-amber-50 border-amber-200',
    muted: 'bg-slate-100 border-slate-200',
    default: 'bg-card',
  }
  const textMap = {
    red: 'text-red-700',
    amber: 'text-amber-700',
    muted: 'text-slate-700',
    default: 'text-foreground',
  }
  return (
    <Card className={cn(bgMap[variant], variant !== 'default' && 'border')}>
      <CardHeader className="pb-2">
        <CardTitle className={cn('text-xs font-medium uppercase tracking-wider', variant !== 'default' ? textMap[variant] : 'text-muted-foreground')}>
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={cn('text-3xl font-bold tabular-nums', variant !== 'default' ? textMap[variant] : '')}>
          {value}
        </div>
        {subtitle && (
          <p className={cn('text-xs mt-1', variant !== 'default' ? textMap[variant] + '/60' : 'text-muted-foreground')}>
            {subtitle}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
