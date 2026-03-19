import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { toast } from 'sonner';
import { useForgotPassword } from '../../hooks/useAuth';

const forgotPasswordSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Enter a valid email'),
});

type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPasswordPage() {
  const forgotPassword = useForgotPassword();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    mode: 'onSubmit',
  });

  const onSubmit = async (values: ForgotPasswordFormValues) => {
    try {
      await forgotPassword.mutateAsync(values);
      toast.success('Check your email for a password reset link.');
      reset();
    } catch {
      toast.error('Something went wrong. Please try again.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F5F5F5] dark:bg-[#0F1117]">
      <div className="bg-white dark:bg-[#1C1E26] rounded-xl shadow-sm w-full max-w-sm p-8">
        {/* Heading */}
        <h1 className="text-2xl font-bold text-[#111827] dark:text-[#F9FAFB] mb-1">
          Forgot your password?
        </h1>
        <p className="text-sm text-[#6B7280] dark:text-[#9CA3AF] mb-6">
          Enter your email and we'll send you a reset link.
        </p>

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

          {/* Submit */}
          <button
            type="submit"
            disabled={forgotPassword.isPending}
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
            {forgotPassword.isPending ? 'Sending...' : 'Send reset link'}
            {!forgotPassword.isPending && <ArrowRight className="h-4 w-4" />}
          </button>
        </form>

        {/* Footer */}
        <p className="mt-6 text-center text-sm text-[#6B7280] dark:text-[#9CA3AF]">
          Remembered your password?{' '}
          <Link to="/login" className="text-[#B5880A] hover:underline font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
