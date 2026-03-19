import { useLocation, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  BookOpen,
  Calendar,
  Users,
  Clock,
  ChartBar,
  AlertTriangle,
  MessageSquare,
  MessageCircle,
  Zap,
  Settings,
  Building2,
  Search,
  X,
} from 'lucide-react';

const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { label: 'Academic', icon: BookOpen, path: '/academic' },
  { label: 'Exam Calendar', icon: Calendar, path: '/exam-calendar' },
  { label: 'Teacher Linking', icon: Users, path: '/teacher-linking' },
  { label: 'Classes', icon: BookOpen, path: '/classes' },
  { label: 'Students', icon: Users, path: '/students' },
  { label: 'Attendance', icon: Clock, path: '/attendance' },
  { label: 'Analytics', icon: ChartBar, path: '/analytics' },
  { label: 'Policy Violations', icon: AlertTriangle, path: '/policy-violations' },
  { label: 'Communications', icon: MessageSquare, path: '/communications' },
  { label: 'Feedback', icon: MessageCircle, path: '/feedback' },
  { label: 'Risk Engine', icon: Zap, path: '/risk-engine' },
  { label: 'Interventions', icon: AlertTriangle, path: '/interventions' },
  { label: 'Users Management', icon: Building2, path: '/admin/users' },
  { label: 'Governance', icon: Building2, path: '/governance' },
];

const SEARCH_TAGS = ['Math', 'Science', 'History'];

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
          'fixed top-0 left-0 h-full z-30 flex flex-col bg-white border-r border-[#e2e8f0] transition-transform duration-300',
          'w-[236px]',
          isOpen ? 'translate-x-0' : '-translate-x-full',
          'md:static md:translate-x-0 md:flex',
        ].join(' ')}
        aria-label="Sidebar navigation"
      >
        {/* Header / Logo — 72px tall to align with navbar */}
        <div className="h-[72px] flex items-center justify-between px-4 border-b border-[#e2e8f0] flex-shrink-0">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center justify-center w-8 h-8 rounded-md bg-[#fe0123]">
              <span className="text-white font-bold text-sm leading-none">V</span>
            </span>
            <span className="font-bold text-[#202939] text-base tracking-tight">Vanta LMS</span>
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
        <div className="px-2 pt-3 pb-2">
          <div className="flex items-center gap-2 bg-[#f9f8f5] rounded-xl h-10 px-3 border border-[#e2e8f0]">
            <Search className="h-4 w-4 text-[#697586] flex-shrink-0" />
            <input
              type="text"
              placeholder="Search..."
              className="bg-transparent text-sm text-[#202939] placeholder-[#697586] outline-none flex-1 min-w-0"
              aria-label="Global search"
            />
          </div>
          {/* Tags */}
          <div className="flex flex-wrap gap-1.5 mt-2">
            {SEARCH_TAGS.map((tag) => (
              <span
                key={tag}
                className="text-xs bg-[#f8fafc] border border-[#e2e8f0] text-[#697586] rounded-full px-2 py-0.5 cursor-pointer hover:border-[#a38654] hover:text-[#a38654] transition-colors"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* Nav items */}
        <nav className="flex-1 overflow-y-auto px-2 pb-2" aria-label="Main navigation">
          <ul className="flex flex-col gap-[3px]" role="list">
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
                      'flex items-center gap-3 h-10 px-3 rounded-lg text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-[#f8fafc] border border-[#e3e8ef] text-[#a38654]'
                        : 'text-[#697586] hover:bg-[#f8fafc] hover:text-[#202939] border border-transparent',
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

        {/* Footer — "Settings" per Figma */}
        <div className="px-2 py-3 border-t border-[#e2e8f0]">
          <button className="flex items-center gap-3 h-10 w-full px-3 rounded-lg text-sm font-medium text-[#697586] hover:bg-[#f8fafc] hover:text-[#202939] transition-colors">
            <Settings className="h-4 w-4 flex-shrink-0" />
            <span>Settings</span>
          </button>
        </div>
      </aside>
    </>
  );
}
