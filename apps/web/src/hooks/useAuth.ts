import { useMutation } from '@tanstack/react-query';
import api from '../lib/api';
import { useAuthStore } from '../lib/auth-store';
import type {
  LoginRequest,
  RegisterRequest,
  ForgotPasswordRequest,
  TokenResponse,
  RegisterResponse,
  MessageResponse,
} from '../types/auth';

export function useLogin() {
  const { setAccessToken } = useAuthStore();

  return useMutation<TokenResponse, Error, LoginRequest>({
    mutationFn: async (body) => {
      const { data } = await api.post<TokenResponse>('/auth/login', body);
      return data;
    },
    onSuccess: (data) => {
      setAccessToken(data.access_token);
    },
  });
}

export function useRegister() {
  return useMutation<RegisterResponse, Error, RegisterRequest>({
    mutationFn: async (body) => {
      const { data } = await api.post<RegisterResponse>('/auth/register', body);
      return data;
    },
  });
}

export function useForgotPassword() {
  return useMutation<MessageResponse, Error, ForgotPasswordRequest>({
    mutationFn: async (body) => {
      const { data } = await api.post<MessageResponse>(
        '/auth/forgot-password',
        body
      );
      return data;
    },
  });
}

export function useLogout() {
  const { clearAccessToken, clearUser } = useAuthStore();

  return useMutation<MessageResponse, Error, void>({
    mutationFn: async () => {
      const { data } = await api.post<MessageResponse>('/auth/logout');
      return data;
    },
    onSuccess: () => {
      clearAccessToken();
      clearUser();
    },
    onError: () => {
      // Clear local auth state even if server-side logout fails
      clearAccessToken();
      clearUser();
    },
  });
}
