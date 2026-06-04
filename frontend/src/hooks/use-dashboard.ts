import api from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import type { DashboardStats } from '@/types'

export function useDashboard() {
  return useQuery<DashboardStats>({
    queryKey: ['dashboard'],
    queryFn: () => api.get('/reconciliation/dashboard/').then((r) => r.data),
    refetchInterval: 30_000,
  })
}
