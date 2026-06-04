import api from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import type { Deal, PaginatedResponse } from '@/types'

export function useDeals(filters: Record<string, string> = {}) {
  return useQuery<PaginatedResponse<Deal>>({
    queryKey: ['deals', filters],
    queryFn: () => api.get('/crm/deals/', { params: filters }).then((r) => r.data),
  })
}
