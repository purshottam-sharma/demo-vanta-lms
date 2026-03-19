import {
  BookOpen,
  Calendar,
  Users,
  ChartBar,
  AlertTriangle,
  Zap,
  ChevronRight,
  Building2,
} from 'lucide-react';
import DashboardCard from './DashboardCard';

// ─── Hero Section ─────────────────────────────────────────────────────────────
function HeroSection() {
  const shortcuts = [
    { label: 'Add Student', icon: Users, color: 'bg-[#0ba5ec]' },
    { label: 'Schedule Exam', icon: Calendar, color: 'bg-[#9b8afb]' },
    { label: 'View Analytics', icon: ChartBar, color: 'bg-[#2fc475]' },
    { label: 'Run Risk Scan', icon: Zap, color: 'bg-[#a38654]' },
  ];

  return (
    <div className="rounded-xl border border-[#e2e8f0] bg-[#f9f8f5] p-6">
      <h2 className="text-lg font-bold text-[#202939]">Good morning</h2>
      <p className="text-sm text-[#697586] mt-1 mb-5">
        Here is a quick overview of what needs your attention today.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
        {shortcuts.map(({ label, icon: Icon, color }) => (
          <button
            key={label}
            className="flex flex-row items-center gap-3 h-14 px-5 rounded-xl bg-[#f9f8f5] border border-[#e2e8f0] hover:border-[#a38654] hover:shadow-sm transition-all cursor-pointer group"
          >
            <div className={['w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0', color].join(' ')}>
              <Icon className="h-4 w-4 text-white" />
            </div>
            <span className="text-sm font-medium text-[#202939] group-hover:text-[#a38654] transition-colors text-left">
              {label}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Row 1: 4 Stat Cards ──────────────────────────────────────────────────────
function StatCardsRow() {
  const stats = [
    { title: 'Total Depts', value: '45', subtitle: 'Active departments', trend: { direction: 'up' as const, label: '2 added this term' } },
    { title: 'Teachers', value: '40', subtitle: 'On faculty', trend: { direction: 'up' as const, label: '6 new this month' } },
    { title: 'Students Enrolled', value: '143,445', subtitle: 'Across all grades', trend: { direction: 'neutral' as const, label: 'Stable' } },
    { title: 'Total Subjects', value: '32', subtitle: 'Active courses', trend: { direction: 'up' as const, label: '3 added' } },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      {stats.map((s) => (
        <DashboardCard
          key={s.title}
          title={s.title}
          value={s.value}
          subtitle={s.subtitle}
          trend={s.trend}
        />
      ))}
    </div>
  );
}

// ─── Row 2: School Health Index + AI Alerts ───────────────────────────────────
function HealthAndAlertsRow() {
  const alerts = [
    { label: 'Attendance below 70% — Grade 9B', color: 'bg-[#e37a72]' },
    { label: '3 students missed 5+ assessments', color: 'bg-[#a38654]' },
    { label: 'Policy violation reported — Block C', color: 'bg-[#9b8afb]' },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* School Health Index */}
      <DashboardCard title="School Health Index" className="min-h-[160px]">
        <div className="flex items-end gap-4 mt-1">
          <div className="relative w-20 h-20 flex-shrink-0">
            <svg viewBox="0 0 36 36" className="w-20 h-20 -rotate-90" aria-hidden="true">
              <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e2e8f0" strokeWidth="3" />
              <circle
                cx="18" cy="18" r="15.9" fill="none"
                stroke="#2fc475" strokeWidth="3"
                strokeDasharray="78 100"
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-sm font-bold text-[#202939]">78%</span>
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center gap-2 text-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-[#2fc475] flex-shrink-0" />
              <span className="text-[#697586]">Compliance</span>
              <span className="ml-auto font-semibold text-[#202939]">82%</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-[#0ba5ec] flex-shrink-0" />
              <span className="text-[#697586]">Engagement</span>
              <span className="ml-auto font-semibold text-[#202939]">75%</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="w-2.5 h-2.5 rounded-full bg-[#9b8afb] flex-shrink-0" />
              <span className="text-[#697586]">Performance</span>
              <span className="ml-auto font-semibold text-[#202939]">77%</span>
            </div>
          </div>
        </div>
      </DashboardCard>

      {/* AI Alerts */}
      <DashboardCard title="AI Alerts" className="min-h-[160px]">
        <ul className="flex flex-col gap-2 mt-1">
          {alerts.map((alert) => (
            <li key={alert.label} className="flex items-start gap-2.5">
              <span className={['w-2 h-2 rounded-full mt-1.5 flex-shrink-0', alert.color].join(' ')} aria-hidden="true" />
              <span className="text-sm text-[#202939]">{alert.label}</span>
            </li>
          ))}
        </ul>
      </DashboardCard>
    </div>
  );
}

// ─── Row 3: Compliance + Interventions + Students at Risk ─────────────────────
function ComplianceRow() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Compliance */}
      <DashboardCard title="Compliance" className="min-h-[140px]">
        <div className="flex flex-col gap-2 mt-1">
          {[
            { label: 'Policy Documents', pct: 92, color: 'bg-[#2fc475]' },
            { label: 'Staff Certifications', pct: 68, color: 'bg-[#a38654]' },
            { label: 'Student Records', pct: 87, color: 'bg-[#0ba5ec]' },
          ].map(({ label, pct, color }) => (
            <div key={label}>
              <div className="flex justify-between text-xs text-[#697586] mb-1">
                <span>{label}</span>
                <span className="font-medium text-[#202939]">{pct}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-[#e2e8f0] overflow-hidden">
                <div
                  className={['h-full rounded-full', color].join(' ')}
                  style={{ width: `${pct}%` }}
                  role="progressbar"
                  aria-valuenow={pct}
                  aria-valuemin={0}
                  aria-valuemax={100}
                />
              </div>
            </div>
          ))}
        </div>
      </DashboardCard>

      {/* Interventions */}
      <DashboardCard title="Interventions" value="23" subtitle="Active interventions" className="min-h-[140px]">
        <div className="flex flex-col gap-1.5 mt-auto">
          <div className="flex justify-between text-sm">
            <span className="text-[#697586]">Pending review</span>
            <span className="font-medium text-[#202939]">8</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-[#697586]">In progress</span>
            <span className="font-medium text-[#202939]">11</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-[#697586]">Resolved this week</span>
            <span className="font-medium text-[#2fc475]">4</span>
          </div>
        </div>
      </DashboardCard>

      {/* Students at Risk */}
      <DashboardCard title="Students at Risk" className="min-h-[140px]">
        <div className="flex flex-col gap-2 mt-1">
          {[
            { label: 'High Risk', count: 7, color: 'text-[#e37a72]', dot: 'bg-[#e37a72]' },
            { label: 'Medium Risk', count: 18, color: 'text-[#a38654]', dot: 'bg-[#a38654]' },
            { label: 'Low Risk', count: 34, color: 'text-[#0ba5ec]', dot: 'bg-[#0ba5ec]' },
          ].map(({ label, count, color, dot }) => (
            <div key={label} className="flex items-center gap-2">
              <span className={['w-2.5 h-2.5 rounded-full flex-shrink-0', dot].join(' ')} aria-hidden="true" />
              <span className="text-sm text-[#697586] flex-1">{label}</span>
              <span className={['text-sm font-semibold', color].join(' ')}>{count}</span>
            </div>
          ))}
        </div>
      </DashboardCard>
    </div>
  );
}

// ─── Row 4: Recent Activity + Manage Users ────────────────────────────────────
function ActivityAndUsersRow() {
  const activities = [
    { action: 'New student enrolled', detail: 'Sarah Chen — Grade 10A', time: '2m ago', color: 'bg-[#2fc475]' },
    { action: 'Risk flag raised', detail: 'John Doe — attendance alert', time: '15m ago', color: 'bg-[#e37a72]' },
    { action: 'Exam scheduled', detail: 'Chemistry — Block B, Fri 9AM', time: '1h ago', color: 'bg-[#9b8afb]' },
    { action: 'Intervention closed', detail: 'Case #204 resolved', time: '3h ago', color: 'bg-[#0ba5ec]' },
  ];

  const users = [
    { name: 'Dr. Emily Watts', role: 'Admin', initials: 'EW', color: 'bg-[#9b8afb]' },
    { name: 'James Nkosi', role: 'Teacher', initials: 'JN', color: 'bg-[#0ba5ec]' },
    { name: 'Priya Sharma', role: 'Counselor', initials: 'PS', color: 'bg-[#2fc475]' },
    { name: 'Tom Rivera', role: 'Staff', initials: 'TR', color: 'bg-[#a38654]' },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Recent Activity */}
      <DashboardCard title="Recent Activity" className="min-h-[180px]">
        <ul className="flex flex-col divide-y divide-[#e2e8f0]">
          {activities.map(({ action, detail, time, color }) => (
            <li key={action} className="flex items-start gap-3 py-2.5 first:pt-1">
              <span className={['w-2 h-2 rounded-full mt-1.5 flex-shrink-0', color].join(' ')} aria-hidden="true" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[#202939]">{action}</p>
                <p className="text-xs text-[#697586] truncate">{detail}</p>
              </div>
              <span className="text-xs text-[#697586] flex-shrink-0">{time}</span>
            </li>
          ))}
        </ul>
      </DashboardCard>

      {/* Manage Users */}
      <DashboardCard title="Manage Users" className="min-h-[180px]">
        <ul className="flex flex-col divide-y divide-[#e2e8f0]">
          {users.map(({ name, role, initials, color }) => (
            <li key={name} className="flex items-center gap-3 py-2.5 first:pt-1">
              <div
                className={['w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0', color].join(' ')}
                aria-hidden="true"
              >
                <span className="text-white text-xs font-semibold">{initials}</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[#202939]">{name}</p>
                <p className="text-xs text-[#697586]">{role}</p>
              </div>
              <button
                className="p-1 rounded text-[#697586] hover:text-[#a38654] hover:bg-[#f8fafc] transition-colors"
                aria-label={`Manage ${name}`}
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      </DashboardCard>
    </div>
  );
}

// ─── DashboardBody ────────────────────────────────────────────────────────────
export default function DashboardBody() {
  return (
    <main className="flex-1 overflow-y-auto bg-[#f8fafc] p-6">
      <div className="max-w-7xl mx-auto flex flex-col gap-6">
        {/* Section 1: Hero / Quick Actions */}
        <HeroSection />

        {/* Section 2: 4-card stat row */}
        <StatCardsRow />

        {/* Section 3: 2-card row — Health Index + AI Alerts */}
        <HealthAndAlertsRow />

        {/* Section 4: 3-card row — Compliance, Interventions, Students at Risk */}
        <ComplianceRow />

        {/* Section 5: 2-card row — Recent Activity + Manage Users */}
        <ActivityAndUsersRow />
      </div>
    </main>
  );
}
