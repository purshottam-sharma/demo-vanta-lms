import { useState, forwardRef } from 'react';
import { Eye, EyeOff } from 'lucide-react';

type PasswordInputProps = Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  'type'
>;

export const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(
  ({ className = '', ...props }, ref) => {
    const [visible, setVisible] = useState(false);

    return (
      <div className="relative">
        <input
          {...props}
          ref={ref}
          type={visible ? 'text' : 'password'}
          className={`
            w-full bg-white dark:bg-[#252836]
            border border-[#E2E8F0] dark:border-[#374151]
            text-[#111827] dark:text-[#F9FAFB]
            placeholder-[#6B7280] dark:placeholder-[#9CA3AF]
            rounded-lg h-10 px-3 pr-10
            text-sm
            focus:outline-none focus:ring-2 focus:ring-[#B5880A] focus:border-transparent
            transition-colors duration-150
            ${className}
          `}
        />
        <button
          type="button"
          tabIndex={-1}
          aria-label={visible ? 'Hide password' : 'Show password'}
          onClick={() => setVisible((v) => !v)}
          className="
            absolute inset-y-0 right-0 flex items-center px-3
            text-[#6B7280] dark:text-[#9CA3AF]
            hover:text-[#111827] dark:hover:text-[#F9FAFB]
            focus:outline-none
            transition-colors duration-150
          "
        >
          {visible ? (
            <EyeOff className="h-4 w-4" aria-hidden="true" />
          ) : (
            <Eye className="h-4 w-4" aria-hidden="true" />
          )}
        </button>
      </div>
    );
  }
);

PasswordInput.displayName = 'PasswordInput';
