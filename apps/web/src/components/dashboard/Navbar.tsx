import { Search, Bell, ChevronDown, User, Menu, Home } from 'lucide-react';
import { useCurrentUser } from '../../hooks/useCurrentUser';

interface NavbarProps {
  onMenuClick: () => void;
}

// UISpec: Navbar 1204x72, bg-white, border-bottom #e3e8ef
// Left: Breadcrumb row (flex-1) — Home icon (#a38654) + "Dashboard" 16px font-medium
// Right: Actions row — Search (360x48) + Bell (48x48) + Profile pill (218x48)
// All right-side elements: bg-[#f8fafc] or bg-[#faf8f5], border, rounded-xl
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
    <header
      data-component="navbar"
      className="h-[72px] flex items-center px-4 py-2 bg-white border-b border-[#e3e8ef] flex-shrink-0 gap-4"
    >
      {/* Hamburger — mobile only */}
      <button
        className="md:hidden p-1.5 rounded-lg text-[#697586] hover:text-[#202939] hover:bg-[#f8fafc] transition-colors flex-shrink-0"
        onClick={onMenuClick}
        aria-label="Open sidebar"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Left: Breadcrumb — Home icon (gold) + "Dashboard" text */}
      <div className="flex-1 hidden md:flex items-center gap-2">
        <Home className="h-5 w-5 text-[#a38654] flex-shrink-0" />
        <span className="text-[16px] font-medium text-[#202939]">Dashboard</span>
      </div>

      {/* Spacer on mobile */}
      <div className="flex-1 md:hidden" />

      {/* Right: Search + Bell + Profile */}
      <div className="flex items-center gap-3 flex-shrink-0">
        {/* Search bar — 360x48, bg-[#faf8f5], border-[#f4f0eb], rounded-xl, px-4, gap-[10px] */}
        <div className="hidden md:flex items-center gap-[10px] w-[360px] h-12 bg-[#faf8f5] rounded-xl px-4 border border-[#f4f0eb]">
          <Search className="h-[14px] w-[14px] text-[#4f3b30] flex-shrink-0" />
          <input
            type="text"
            placeholder="Global Search"
            className="bg-transparent text-[14px] font-medium text-[#202939] placeholder-[#898680] outline-none flex-1 min-w-0"
            aria-label="Global search"
          />
        </div>

        {/* Notification bell — 48x48, bg-[#f8fafc], border-[#e3e8ef], rounded-xl */}
        <button
          className="w-12 h-12 bg-[#f8fafc] rounded-xl flex items-center justify-center text-[#202939] border border-[#e3e8ef] hover:text-[#a38654] transition-colors flex-shrink-0"
          aria-label="Notifications"
        >
          <Bell className="h-[18px] w-[18px]" />
        </button>

        {/* Profile pill — 218x48, bg-[#f8fafc], border-[#e3e8ef], rounded-xl, p-2 gap-2 */}
        <div className="flex items-center gap-2 w-[218px] h-12 bg-[#f8fafc] rounded-xl px-2 border border-[#e3e8ef] flex-shrink-0">
          {/* Avatar circle — 32x32, rounded-full, border-[#e3e8ef], icon color #a38654 */}
          <div
            className="w-8 h-8 rounded-full bg-[#f8fafc] border border-[#e3e8ef] flex items-center justify-center flex-shrink-0"
            aria-hidden="true"
          >
            {isLoading ? (
              <User className="h-3.5 w-3.5 text-[#a38654]" />
            ) : initials ? (
              <span className="text-[#a38654] text-[11px] font-semibold">{initials}</span>
            ) : (
              <User className="h-3.5 w-3.5 text-[#a38654]" />
            )}
          </div>
          {/* User name — 14px font-semibold */}
          <div className="flex-1 min-w-0">
            {isLoading ? (
              <span className="text-[14px] text-[#697586] animate-pulse">Loading...</span>
            ) : (
              <span className="text-[14px] font-semibold text-[#202939] truncate block">
                {user?.full_name ?? 'Khalid Al Sabah'}
              </span>
            )}
          </div>
          <ChevronDown className="h-[14px] w-[14px] text-[#697586] flex-shrink-0" />
        </div>
      </div>
    </header>
  );
}
