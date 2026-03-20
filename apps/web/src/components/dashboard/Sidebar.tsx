import { useLocation, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  School,
  CalendarClock,
  Link2,
  BookOpen,
  GraduationCap,
  UserCheck,
  TrendingUp,
  FileWarning,
  MessageSquare,
  Mail,
  Zap,
  Lightbulb,
  UserCog,
  Landmark,
  Settings,
  Search,
  X,
} from 'lucide-react';

// UISpec: 15 nav items + Settings footer
const NAV_ITEMS = [
  { label: 'Dashboard',       icon: LayoutDashboard, path: '/dashboard' },
  { label: 'Academic',        icon: School,          path: '/academic' },
  { label: 'Exam Calendar',   icon: CalendarClock,   path: '/exam-calendar' },
  { label: 'Teacher Linking', icon: Link2,           path: '/teacher-linking' },
  { label: 'Classes',         icon: BookOpen,        path: '/classes' },
  { label: 'Students',        icon: GraduationCap,   path: '/students' },
  { label: 'Attendance',      icon: UserCheck,       path: '/attendance' },
  { label: 'Analytics',       icon: TrendingUp,      path: '/analytics' },
  { label: 'Policy Violations',icon: FileWarning,    path: '/policy-violations' },
  { label: 'Communications',  icon: MessageSquare,   path: '/communications' },
  { label: 'Feedback',        icon: Mail,            path: '/feedback' },
  { label: 'Risk Engine',     icon: Zap,             path: '/risk-engine' },
  { label: 'Interventions',   icon: Lightbulb,       path: '/interventions' },
  { label: 'Users Management',icon: UserCog,         path: '/admin/users' },
  { label: 'Governance',      icon: Landmark,        path: '/governance' },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation();

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar panel — 236px wide, full height */}
      <aside
        data-component="sidebar"
        className={[
          'fixed top-0 left-0 h-full z-30 flex flex-col bg-white border-r border-[#e3e8ef] transition-transform duration-300',
          'w-[236px]',
          isOpen ? 'translate-x-0' : '-translate-x-full',
          'md:static md:translate-x-0 md:flex',
        ].join(' ')}
        aria-label="Sidebar navigation"
      >
        {/* Header — 72px tall per Figma (UISpec: h=72, padding 8px 16px, gap=8) */}
        <div className="h-[72px] flex items-center justify-between px-4 py-2 border-b border-[#e3e8ef] flex-shrink-0">
          <div className="flex items-center gap-2">
            {/* 4-quadrant colored grid icon */}
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <rect x="2"  y="2"  width="9" height="9" rx="1" fill="#22c55e" />
              <rect x="13" y="2"  width="9" height="9" rx="1" fill="#f59e0b" />
              <rect x="2"  y="13" width="9" height="9" rx="1" fill="#e37a72" />
              <rect x="13" y="13" width="9" height="9" rx="1" fill="#3b82f6" />
            </svg>
            <span className="font-semibold text-[#202939] text-sm tracking-tight">Vanta LMS</span>
          </div>
          {/* Close button — mobile only */}
          <button
            className="md:hidden p-1 rounded text-[#697586] hover:text-[#202939] hover:bg-[#f8fafc] transition-colors"
            onClick={onClose}
            aria-label="Close sidebar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Sidebar Body — p-2 (8px), gap-3 (12px) per UISpec */}
        <div className="flex flex-col gap-3 p-2 flex-1 min-h-0">
          {/* Search bar — 220x40, rounded-xl, border #e3e8ef, padding 12px, gap 10 */}
          <div className="flex items-center gap-[10px] bg-white rounded-xl h-10 px-3 border border-[#e3e8ef]">
            <Search className="h-5 w-5 text-[#9aa4b2] flex-shrink-0" />
            <input
              type="text"
              placeholder="Global Search"
              className="bg-transparent text-[14px] text-[#202939] placeholder-[#898680] outline-none flex-1 min-w-0"
              aria-label="Global search"
            />
            {/* "/" shortcut pill: 20x20, bg-[#f8fafc], border, r=4, gold text */}
            <div className="w-5 h-5 rounded bg-[#f8fafc] border border-[#e3e8ef] flex items-center justify-center flex-shrink-0">
              <span className="text-[12px] font-medium text-[#a38654] leading-none">/</span>
            </div>
          </div>

          {/* Nav items — flex-col gap-[2px] per UISpec */}
          <nav className="flex-1 overflow-y-auto" aria-label="Main navigation">
            <ul className="flex flex-col gap-[2px]" role="list">
              {NAV_ITEMS.map(({ label, icon: Icon, path }) => {
                const isActive =
                  path === '/dashboard'
                    ? location.pathname === '/dashboard' || location.pathname === '/'
                    : location.pathname === path;

                return (
                  <li key={label}>
                    <Link
                      to={path}
                      className={[
                        // UISpec: h=40, px-3 py-3 gap-3, rounded-lg, text-[14px]
                        'flex items-center gap-3 h-10 px-3 rounded-lg text-[14px] transition-colors',
                        isActive
                          ? 'bg-[#f8fafc] border border-[#e3e8ef] text-[#a38654] font-medium'
                          : 'text-[#697586] font-normal hover:bg-[#f8fafc] hover:text-[#202939] border border-transparent',
                      ].join(' ')}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      {/* Icon: h-5 w-5, inactive color #9aa4b2, active color #a38654 */}
                      <Icon
                        className="h-5 w-5 flex-shrink-0"
                        style={{ color: isActive ? '#a38654' : '#9aa4b2' }}
                      />
                      <span>{label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>

        {/* Footer — Settings button, border-top, p-2 */}
        <div className="px-2 py-2 border-t border-[#e3e8ef] flex-shrink-0">
          <button className="flex items-center gap-3 h-10 w-full px-3 rounded-lg text-[14px] font-normal text-[#697586] hover:bg-[#f8fafc] hover:text-[#202939] transition-colors">
            <Settings className="h-5 w-5 flex-shrink-0" style={{ color: '#9aa4b2' }} />
            <span>Settings</span>
          </button>
        </div>
      </aside>
    </>
  );
}
