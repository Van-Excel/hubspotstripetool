import api from '@/lib/api'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { User, PaginatedResponse } from '@/types'

export function useUsers(filters: Record<string, string> = {}) {
  return useQuery<PaginatedResponse<User>>({
    queryKey: ['users', filters],
    queryFn: () => api.get('/admin/users/', { params: filters }).then((r) => r.data),
  })
}

export function useUpdateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      api.patch(`/admin/users/${id}/`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
    },
  })
}
