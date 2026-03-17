import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

export function useDocuments() {
  const qc = useQueryClient()
  const list = useQuery({ queryKey: ['documents'], queryFn: api.documents.list })
  const del = useMutation({
    mutationFn: (id: string) => api.documents.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  })
  return { documents: list.data ?? [], isLoading: list.isLoading, deleteDoc: del.mutate }
}
