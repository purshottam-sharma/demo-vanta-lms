import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import type {
  AdminUser,
  PaginatedUsersResponse,
  UpdateRolePayload,
  UpdateStatusPayload,
} from '../types/admin';

interface UseAdminUsersParams {
  search: string;
  role: string;
  page: number;
  pageSize: number;
}

export function useAdminUsers({ search, role, page, pageSize }: UseAdminUsersParams) {
  return useQuery<PaginatedUsersResponse>({
    queryKey: ['adminUsers', { search, role, page, pageSize }],
    queryFn: async () => {
      const params: Record<string, string | number> = {
        page,
        page_size: pageSize,
      };
      if (search) params.search = search;
      if (role && role !== 'All') params.role = role;

      const { data } = await api.get<PaginatedUsersResponse>('/admin/users', { params });
      return data;
    },
    placeholderData: (prev) => prev,
  });
}

interface UpdateRoleMutationVariables {
  userId: string;
  payload: UpdateRolePayload;
}

export function useUpdateUserRole() {
  const queryClient = useQueryClient();

  return useMutation<AdminUser, Error, UpdateRoleMutationVariables>({
    mutationFn: async ({ userId, payload }) => {
      const { data } = await api.patch<AdminUser>(`/admin/users/${userId}/role`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminUsers'] });
    },
  });
}

interface UpdateStatusMutationVariables {
  userId: string;
  payload: UpdateStatusPayload;
}

export function useUpdateUserStatus() {
  const queryClient = useQueryClient();

  return useMutation<AdminUser, Error, UpdateStatusMutationVariables>({
    mutationFn: async ({ userId, payload }) => {
      const { data } = await api.patch<AdminUser>(`/admin/users/${userId}/status`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminUsers'] });
    },
  });
}
