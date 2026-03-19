import { ReactNode } from 'react';

interface DashboardCardProps {
  title?: string;
  value?: string | number;
  subtitle?: string;
  trend?: {
    direction: 'up' | 'down' | 'neutral';
    label: string;
  };
  children?: ReactNode;
  className?: string;
  altBg?: boolean;
}

export default function DashboardCard({
  title,
  value,
  subtitle,
  trend,
  children,
  className = '',
  altBg = false,
}: DashboardCardProps) {
  const trendColors: Record<string, string> = {
    up: 'text-[#2fc475]',
    down: 'text-[#e37a72]',
    neutral: 'text-[#697586]',
  };

  return (
    <div
      className={[
        'rounded-xl border border-[#e2e8f0] p-5 flex flex-col gap-2',
        altBg ? 'bg-[#f9f8f5]' : 'bg-white',
        className,
      ].join(' ')}
    >
      {title && (
        <p className="text-sm font-medium text-[#697586]">{title}</p>
      )}

      {value !== undefined && (
        <p className="text-[32px] leading-none font-semibold text-[#202939]">{value}</p>
      )}

      {subtitle && (
        <p className="text-sm text-[#697586]">{subtitle}</p>
      )}

      {trend && (
        <span className={['text-xs font-medium', trendColors[trend.direction]].join(' ')}>
          {trend.direction === 'up' ? '↑' : trend.direction === 'down' ? '↓' : '→'}{' '}
          {trend.label}
        </span>
      )}

      {children}
    </div>
  );
}
