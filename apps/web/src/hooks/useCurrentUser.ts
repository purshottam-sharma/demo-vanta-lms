import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import { useAuthStore } from '../lib/auth-store';
import type { AuthUser } from '../types/auth';

interface CurrentUserResponse {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

export function useCurrentUser() {
  const accessToken = useAuthStore((s) => s.accessToken);

  return useQuery<AuthUser>({
    queryKey: ['currentUser'],
    queryFn: async () => {
      const { data } = await api.get<CurrentUserResponse>('/users/me');
      return {
        id: data.id,
        email: data.email,
        full_name: data.full_name,
      };
    },
    enabled: !!accessToken,
    staleTime: 1000 * 60 * 5,
  });
}
