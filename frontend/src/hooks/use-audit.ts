import api from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import type { AuditLog, PaginatedResponse } from '@/types'

export function useAuditLogs(filters: Record<string, string> = {}) {
  return useQuery<PaginatedResponse<AuditLog>>({
    queryKey: ['auditLogs', filters],
    queryFn: () => api.get('/audit/logs/', { params: filters }).then((r) => r.data),
  })
}
