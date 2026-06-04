import api from '@/lib/api'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { Anomaly, PaginatedResponse } from '@/types'

interface AnomalyFilters {
  anomaly_type?: string
  severity?: string
  page?: number
}

export function useAnomalies(filters: AnomalyFilters = {}) {
  return useQuery<PaginatedResponse<Anomaly>>({
    queryKey: ['anomalies', filters],
    queryFn: () => api.get('/reconciliation/anomalies/', { params: filters }).then((r) => r.data),
  })
}

export function useResolveAnomaly() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { resolution_type: string; notes: string } }) =>
      api.post(`/reconciliation/anomalies/${id}/resolve/`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['anomalies'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}
