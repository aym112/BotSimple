import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './client'
import type { QueryResponse, TraceResponse } from './types'

interface Me {
  username: string
}

export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: () => api.get<Me>('/auth/me'),
    retry: false,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (credentials: { username: string; password: string }) =>
      api.post<Me>('/auth/login', credentials),
    onSuccess: (me) => {
      queryClient.setQueryData(['me'], me)
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => api.post('/auth/logout'),
    onSuccess: () => {
      queryClient.setQueryData(['me'], null)
      queryClient.clear()
    },
  })
}

export function useSubmitQuery() {
  return useMutation({
    mutationFn: (question: string) => api.post<QueryResponse>('/api/v1/query', { question }),
  })
}

export function useDocumentMarkdown(filename: string | null) {
  return useQuery({
    queryKey: ['document-markdown', filename],
    queryFn: () => api.getText(`/api/v1/documents/${encodeURIComponent(filename!)}/markdown`),
    enabled: filename !== null,
  })
}

export function useTrace(requestId: string | null) {
  return useQuery({
    queryKey: ['trace', requestId],
    queryFn: () => api.get<TraceResponse>(`/api/v1/requests/${requestId}/trace`),
    enabled: requestId !== null,
  })
}
