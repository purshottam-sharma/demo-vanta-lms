import React from 'react';

interface SocialButtonProps {
  onClick?: () => void;
  children: React.ReactNode;
  disabled?: boolean;
  type?: 'button' | 'submit';
}

export function SocialButton({
  onClick,
  children,
  disabled = false,
  type = 'button',
}: SocialButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className="
        border border-[#E2E8F0] dark:border-[#374151]
        bg-white dark:bg-[#252836]
        text-[#111827] dark:text-[#F9FAFB]
        w-full rounded-lg h-10
        flex items-center justify-center gap-2
        text-sm font-medium
        hover:bg-gray-50 dark:hover:bg-[#2d3044]
        transition-colors duration-150
        disabled:opacity-50 disabled:cursor-not-allowed
        focus:outline-none focus:ring-2 focus:ring-[#B5880A] focus:ring-offset-1
      "
    >
      {children}
    </button>
  );
}
