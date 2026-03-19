import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { AuthUser } from '../types/auth';

interface AuthState {
  accessToken: string | null;
  user: AuthUser | null;
  setAccessToken: (token: string) => void;
  clearAccessToken: () => void;
  setUser: (user: AuthUser) => void;
  clearUser: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      user: null,
      setAccessToken: (token) => set({ accessToken: token }),
      clearAccessToken: () => set({ accessToken: null }),
      setUser: (user) => set({ user }),
      clearUser: () => set({ user: null }),
    }),
    {
      name: 'vanta-auth',
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({ accessToken: state.accessToken }),
    }
  )
);
