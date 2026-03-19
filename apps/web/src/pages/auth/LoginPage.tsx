import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { toast } from 'sonner';
import { useLogin } from '../../hooks/useAuth';
import { SocialButton } from '../../components/auth/SocialButton';
import { AuthDivider } from '../../components/auth/AuthDivider';
import { PasswordInput } from '../../components/auth/PasswordInput';

const loginSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

// Google SVG icon (official colors)
function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 0 0 2.38-5.88c0-.57-.05-.66-.15-1.18z"
      />
      <path
        fill="#34A853"
        d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2.04a4.8 4.8 0 0 1-7.18-2.53H1.83v2.07A8 8 0 0 0 8.98 17z"
      />
      <path
        fill="#FBBC05"
        d="M4.5 10.49a4.8 4.8 0 0 1 0-3v-2.07H1.83a8 8 0 0 0 0 7.14z"
      />
      <path
        fill="#EA4335"
        d="M8.98 4.72a4.36 4.36 0 0 1 3.08 1.2l2.3-2.3A7.74 7.74 0 0 0 8.98 1 8 8 0 0 0 1.83 5.42l2.67 2.07a4.77 4.77 0 0 1 4.48-2.77z"
      />
    </svg>
  );
}

// Apple SVG icon
function AppleIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 814 1000"
      aria-hidden="true"
      className="fill-[#111827] dark:fill-[#F9FAFB]"
    >
      <path d="M788.1 340.9c-5.8 4.5-108.2 62.2-108.2 190.5 0 148.4 130.3 200.9 134.2 202.2-.6 3.2-20.7 71.9-68.7 141.9-42.8 61.6-87.5 123.1-155.5 123.1s-85.5-39.5-164-39.5c-76 0-103.7 40.8-165.9 40.8s-105-57.8-155.5-127.4C46 465.5 0 300.3 0 282.3c0-22.5 8.6-44.5 19.7-62.4 29.7-47.5 80.5-78.1 134.8-78.1 48.1 0 88.3 32.7 116.9 32.7 28 0 73.6-34.4 130.9-34.4 22 0 100.2 1.9 157.5 75.5zM469.2 134.5c24.4-29.4 41.6-69.7 41.6-110 0-5.8-.6-11.6-1.9-16.4-38.1 1.4-83.6 26.5-110.4 58.6-21.1 24.8-40.9 63.1-40.9 104.6 0 6.4.6 12.5 1.3 17.6 2.6.6 5.2.9 7.8.9 34.4 0 77.7-24.7 102.5-55.3z" />
    </svg>
  );
}

export default function LoginPage() {
  const navigate = useNavigate();
  const login = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    mode: 'onSubmit',
  });

  const onSubmit = async (values: LoginFormValues) => {
    try {
      await login.mutateAsync(values);
      navigate('/');
    } catch {
      toast.error('Invalid email or password. Please try again.');
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = '/api/v1/auth/google';
  };

  const handleAppleLogin = () => {
    window.location.href = '/api/v1/auth/apple';
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F5F5F5] dark:bg-[#0F1117]">
      <div className="bg-white dark:bg-[#1C1E26] rounded-xl shadow-sm w-full max-w-sm p-8">
        {/* Heading */}
        <h1 className="text-2xl font-bold text-[#111827] dark:text-[#F9FAFB] mb-1">
          Welcome back
        </h1>
        <p className="text-sm text-[#6B7280] dark:text-[#9CA3AF] mb-6">
          Sign in to your account
        </p>

        {/* Social buttons */}
        <div className="flex flex-col gap-3 mb-2">
          <SocialButton onClick={handleGoogleLogin}>
            <GoogleIcon />
            <span>Continue with Google</span>
          </SocialButton>
          <SocialButton onClick={handleAppleLogin}>
            <AppleIcon />
            <span>Continue with Apple</span>
          </SocialButton>
        </div>

        <AuthDivider />

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
          {/* Email */}
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-[#111827] dark:text-[#F9FAFB] mb-1"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              {...register('email')}
              aria-describedby={errors.email ? 'email-error' : undefined}
              className="
                w-full bg-white dark:bg-[#252836]
                border border-[#E2E8F0] dark:border-[#374151]
                text-[#111827] dark:text-[#F9FAFB]
                placeholder-[#6B7280] dark:placeholder-[#9CA3AF]
                rounded-lg h-10 px-3
                text-sm
                focus:outline-none focus:ring-2 focus:ring-[#B5880A] focus:border-transparent
                transition-colors duration-150
              "
            />
            {errors.email && (
              <p
                id="email-error"
                role="alert"
                className="mt-1 text-xs text-red-500 dark:text-red-400"
              >
                {errors.email.message}
              </p>
            )}
          </div>

          {/* Password */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label
                htmlFor="password"
                className="block text-sm font-medium text-[#111827] dark:text-[#F9FAFB]"
              >
                Password
              </label>
              <Link
                to="/forgot-password"
                className="text-xs text-[#B5880A] hover:underline"
              >
                Forgot your password?
              </Link>
            </div>
            <PasswordInput
              id="password"
              autoComplete="current-password"
              placeholder="********"
              {...register('password')}
              aria-describedby={errors.password ? 'password-error' : undefined}
            />
            {errors.password && (
              <p
                id="password-error"
                role="alert"
                className="mt-1 text-xs text-red-500 dark:text-red-400"
              >
                {errors.password.message}
              </p>
            )}
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={login.isPending}
            className="
              bg-[#B5880A] hover:bg-[#9A7309]
              text-white
              w-full rounded-lg h-10
              font-semibold
              flex items-center justify-center gap-2
              transition-colors duration-150
              disabled:opacity-60 disabled:cursor-not-allowed
              focus:outline-none focus:ring-2 focus:ring-[#B5880A] focus:ring-offset-2
              mt-2
            "
          >
            {login.isPending ? 'Signing in...' : 'Sign in'}
            {!login.isPending && <ArrowRight className="h-4 w-4" />}
          </button>
        </form>

        {/* Footer */}
        <p className="mt-6 text-center text-sm text-[#6B7280] dark:text-[#9CA3AF]">
          Don't have an account?{' '}
          <Link to="/register" className="text-[#B5880A] hover:underline font-medium">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
