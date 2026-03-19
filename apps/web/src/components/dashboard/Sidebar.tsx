import { useLocation, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  GraduationCap,
  Calendar,
  Users,
  BookOpen,
  UserCheck,
  ClipboardCheck,
  BarChart2,
  AlertTriangle,
  MessageSquare,
  ThumbsUp,
  ShieldAlert,
  Activity,
  UserCog,
  Landmark,
  Settings,
  Search,
  X,
} from 'lucide-react';

const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { label: 'Academic', icon: GraduationCap, path: '/academic' },
  { label: 'Exam Calendar', icon: Calendar, path: '/exam-calendar' },
  { label: 'Teacher Loading', icon: Users, path: '/teacher-linking' },
  { label: 'Classes', icon: BookOpen, path: '/classes' },
  { label: 'Students', icon: UserCheck, path: '/students' },
  { label: 'Attendance', icon: ClipboardCheck, path: '/attendance' },
  { label: 'Analytics', icon: BarChart2, path: '/analytics' },
  { label: 'Policy Violations', icon: AlertTriangle, path: '/policy-violations' },
  { label: 'Communications', icon: MessageSquare, path: '/communications' },
  { label: 'Feedback', icon: ThumbsUp, path: '/feedback' },
  { label: 'Risk Engine', icon: ShieldAlert, path: '/risk-engine' },
  { label: 'Interventions', icon: Activity, path: '/interventions' },
  { label: 'Users Management', icon: UserCog, path: '/admin/users' },
  { label: 'Governance', icon: Landmark, path: '/governance' },
];

const SEARCH_TAGS = ['Academic', 'Administrative'];

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

      {/* Sidebar panel */}
      <aside
        className={[
          'fixed top-0 left-0 h-full z-30 flex flex-col bg-white border-r border-[#e3e8ef] transition-transform duration-300',
          'w-[236px]',
          isOpen ? 'translate-x-0' : '-translate-x-full',
          'md:static md:translate-x-0 md:flex',
        ].join(' ')}
        aria-label="Sidebar navigation"
      >
        {/* Header / Logo — 60px tall per Figma */}
        <div className="h-[60px] flex items-center justify-between px-4 border-b border-[#e3e8ef] flex-shrink-0">
          <div className="flex items-center gap-2">
            {/* 4-quadrant colored grid icon (Windows-logo style) */}
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <rect x="2" y="2" width="9" height="9" rx="1" fill="#22c55e" />
              <rect x="13" y="2" width="9" height="9" rx="1" fill="#f59e0b" />
              <rect x="2" y="13" width="9" height="9" rx="1" fill="#e37a72" />
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

        {/* Search */}
        <div className="mx-3 mt-3 mb-2">
          <div className="flex items-center gap-2 bg-[#f9f8f5] rounded-lg h-9 px-[10px] border border-[#e3e8ef]">
            <Search className="h-[14px] w-[14px] text-[#697586] flex-shrink-0" />
            <input
              type="text"
              placeholder="Global Search"
              className="bg-transparent text-[13px] text-[#202939] placeholder-[#697586] outline-none flex-1 min-w-0"
              aria-label="Global search"
            />
          </div>
          {/* Tags */}
          <div className="flex flex-wrap gap-1 mt-2">
            {SEARCH_TAGS.map((tag) => (
              <span
                key={tag}
                className="text-[11px] bg-[#f1f5f9] text-[#697586] rounded-full px-2 py-0.5 cursor-pointer hover:text-[#a38654] transition-colors"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* Nav items */}
        <nav className="flex-1 overflow-y-auto px-2 py-1" aria-label="Main navigation">
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
                      'flex items-center gap-2 h-9 px-[10px] rounded-lg text-[13px] transition-colors',
                      isActive
                        ? 'bg-[#f8f6f0] border border-[#e3e8ef] text-[#a38654] font-medium'
                        : 'text-[#697586] font-normal hover:bg-[#f8fafc] hover:text-[#202939] border border-transparent',
                    ].join(' ')}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <Icon className="h-4 w-4 flex-shrink-0" />
                    <span>{label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer — Settings per Figma */}
        <div className="px-2 py-2 border-t border-[#e3e8ef]">
          <button className="flex items-center gap-2 h-9 w-full px-[10px] rounded-lg text-[13px] font-normal text-[#697586] hover:bg-[#f8fafc] hover:text-[#202939] transition-colors">
            <Settings className="h-4 w-4 flex-shrink-0" />
            <span>Settings</span>
          </button>
        </div>
      </aside>
    </>
  );
}
