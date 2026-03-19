import { Search, Bell, ChevronDown, User, Menu } from 'lucide-react';
import { useCurrentUser } from '../../hooks/useCurrentUser';

interface NavbarProps {
  onMenuClick: () => void;
}

export default function Navbar({ onMenuClick }: NavbarProps) {
  const { data: user, isLoading } = useCurrentUser();

  const initials = user?.full_name
    ? user.full_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : null;

  return (
    <header className="h-[72px] flex items-center px-6 bg-white border-b border-[#e2e8f0] flex-shrink-0 gap-4">
      {/* Hamburger — mobile only */}
      <button
        className="md:hidden p-1.5 rounded-lg text-[#697586] hover:text-[#202939] hover:bg-[#f8fafc] transition-colors flex-shrink-0"
        onClick={onMenuClick}
        aria-label="Open sidebar"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Search bar — fills available space, max 360px per Figma */}
      <div className="flex-1 hidden md:flex">
        <div className="flex items-center gap-3 w-[360px] h-12 bg-[#f9f8f5] rounded-xl px-4 border border-[#e2e8f0]">
          <Search className="h-4 w-4 text-[#697586] flex-shrink-0" />
          <input
            type="text"
            placeholder="Search..."
            className="bg-transparent text-sm text-[#202939] placeholder-[#697586] outline-none flex-1 min-w-0"
            aria-label="Global search"
          />
        </div>
      </div>

      {/* Spacer on mobile */}
      <div className="flex-1 md:hidden" />

      {/* Right actions */}
      <div className="flex items-center gap-3 flex-shrink-0">
        {/* Notification bell — 48×48, bg #f8fafc, radius 12 */}
        <button
          className="relative w-12 h-12 bg-[#f8fafc] rounded-xl flex items-center justify-center text-[#697586] hover:text-[#202939] border border-[#e2e8f0] transition-colors flex-shrink-0"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
          <span
            className="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-[#e37a72] border-2 border-white"
            aria-hidden="true"
          />
        </button>

        {/* Profile pill — 218×48, bg #f8fafc, radius 12, gap 8, padding 8 */}
        <div className="flex items-center gap-2 w-[218px] h-12 bg-[#f8fafc] rounded-xl px-2 border border-[#e2e8f0] flex-shrink-0">
          <div
            className="w-8 h-8 rounded-full bg-[#a38654] flex items-center justify-center flex-shrink-0"
            aria-hidden="true"
          >
            {isLoading ? (
              <User className="h-4 w-4 text-white" />
            ) : initials ? (
              <span className="text-white text-xs font-semibold">{initials}</span>
            ) : (
              <User className="h-4 w-4 text-white" />
            )}
          </div>
          <div className="flex flex-col flex-1 min-w-0">
            {isLoading ? (
              <span className="text-xs text-[#697586] animate-pulse">Loading...</span>
            ) : (
              <>
                <span className="text-sm font-medium text-[#202939] truncate">
                  {user?.full_name ?? 'User'}
                </span>
                <span className="text-xs text-[#697586] truncate">{user?.email ?? ''}</span>
              </>
            )}
          </div>
          <ChevronDown className="h-4 w-4 text-[#697586] flex-shrink-0" />
        </div>
      </div>
    </header>
  );
}
