import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import { Toaster } from 'sonner';
import { useAuthStore } from './lib/auth-store';
import { useLogout } from './hooks/useAuth';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
});

/**
 * Route guard: redirects unauthenticated users to /login.
 * Access token is held in memory (Zustand) - not localStorage.
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const accessToken = useAuthStore((s) => s.accessToken);
  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

/**
 * Placeholder for the authenticated dashboard / home.
 * Replace with the real dashboard component once built.
 */
function DashboardPage() {
  const { mutate: logout, isPending } = useLogout();
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F5F5F5] dark:bg-[#0F1117]">
      <div className="bg-white dark:bg-[#1C1E26] rounded-xl shadow-sm w-full max-w-sm p-8">
        <h1 className="text-2xl font-bold text-[#111827] dark:text-[#F9FAFB]">
          Vanta LMS
        </h1>
        <p className="mt-2 text-sm text-[#6B7280] dark:text-[#9CA3AF]">
          You are signed in.
        </p>
        <button
          onClick={() => logout()}
          disabled={isPending}
          className="mt-6 w-full py-2 px-4 rounded-lg text-sm font-medium text-white bg-[#B5880A] hover:bg-[#9a7309] disabled:opacity-50 transition-colors"
        >
          {isPending ? 'Signing out...' : 'Sign out'}
        </button>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public auth routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />

          {/* Protected routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />

          {/* Catch-all: redirect unknown paths to login */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>

        {/* Sonner toast container - renders toasts from all pages */}
        <Toaster richColors position="top-right" />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
