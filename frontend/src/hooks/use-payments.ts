import api from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import type { PaymentTransaction, PaginatedResponse } from '@/types'

export function usePayments(filters: Record<string, string> = {}) {
  return useQuery<PaginatedResponse<PaymentTransaction>>({
    queryKey: ['payments', filters],
    queryFn: () => api.get('/payments/', { params: filters }).then((r) => r.data),
  })
}
