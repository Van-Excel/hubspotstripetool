import api from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import type { Customer, PaginatedResponse } from '@/types'

export function useCustomers(filters: Record<string, string> = {}) {
  return useQuery<PaginatedResponse<Customer>>({
    queryKey: ['customers', filters],
    queryFn: () => api.get('/crm/customers/', { params: filters }).then((r) => r.data),
  })
}
