import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

export function useReports() {
  const qc = useQueryClient()
  const list = useQuery({ queryKey: ['reports'], queryFn: api.reports.list })
  const del = useMutation({
    mutationFn: (id: string) => api.reports.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reports'] }),
  })
  return { reports: list.data ?? [], isLoading: list.isLoading, deleteReport: del.mutate }
}
