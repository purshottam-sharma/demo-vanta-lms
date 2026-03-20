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
    <header data-component="navbar" className="h-[56px] flex items-center px-6 bg-white border-b border-[#e3e8ef] flex-shrink-0 gap-4">
      {/* Hamburger — mobile only */}
      <button
        className="md:hidden p-1.5 rounded-lg text-[#697586] hover:text-[#202939] hover:bg-[#f8fafc] transition-colors flex-shrink-0"
        onClick={onMenuClick}
        aria-label="Open sidebar"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Page title — left zone */}
      <h1 className="hidden md:block text-base font-semibold text-[#202939] flex-shrink-0">
        Dashboard
      </h1>

      {/* Search bar — flex-1, fills available space between title and right controls */}
      <div className="flex-1 hidden md:flex">
        <div className="flex items-center gap-2 w-full max-w-[360px] h-10 bg-[#f9f8f5] rounded-[10px] px-3 border border-[#e3e8ef]">
          <Search className="h-[14px] w-[14px] text-[#697586] flex-shrink-0" />
          <input
            type="text"
            placeholder="Search..."
            className="bg-transparent text-[13px] text-[#202939] placeholder-[#697586] outline-none flex-1 min-w-0"
            aria-label="Global search"
          />
        </div>
      </div>

      {/* Spacer on mobile */}
      <div className="flex-1 md:hidden" />

      {/* Right actions */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {/* Notification bell — 40×40, rounded-[10px], NO badge dot per Figma */}
        <button
          className="w-12 h-12 bg-[#f8fafc] rounded-xl flex items-center justify-center text-[#697586] hover:text-[#202939] border border-[#e3e8ef] transition-colors flex-shrink-0"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
        </button>

        {/* Profile pill — 180×40, bg #f8fafc, rounded-[10px], gap 8, padding 10 */}
        <div className="flex items-center gap-2 w-[218px] h-12 bg-[#f8fafc] rounded-xl px-[10px] border border-[#e3e8ef] flex-shrink-0">
          <div
            className="w-7 h-7 rounded-full bg-[#e2e8f0] flex items-center justify-center flex-shrink-0"
            aria-hidden="true"
          >
            {isLoading ? (
              <User className="h-3.5 w-3.5 text-[#697586]" />
            ) : initials ? (
              <span className="text-[#697586] text-[11px] font-semibold">{initials}</span>
            ) : (
              <User className="h-3.5 w-3.5 text-[#697586]" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            {isLoading ? (
              <span className="text-[13px] text-[#697586] animate-pulse">Loading...</span>
            ) : (
              <span className="text-[13px] font-medium text-[#202939] truncate block">
                {user?.full_name ?? 'User'}
              </span>
            )}
          </div>
          <ChevronDown className="h-[14px] w-[14px] text-[#697586] flex-shrink-0" />
        </div>
      </div>
    </header>
  );
}
