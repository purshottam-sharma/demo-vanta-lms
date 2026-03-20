import {
  UserPlus,
  Building2,
  ShieldCheck,
  Download,
  Building,
  GraduationCap,
  Users,
  BookOpen,
  ChevronRight,
  TrendingUp,
  Brain,
  Activity,
  AlertTriangle,
  ShieldAlert,
  ArrowUpDown,
} from 'lucide-react';

// ─── Quick Actions Section ─────────────────────────────────────────────────────
function QuickActionsSection() {
  const actions = [
    { label: 'Add User', icon: UserPlus, iconBg: '#eff6ff', iconColor: '#3b82f6' },
    { label: 'New Institution', icon: Building2, iconBg: '#fffbeb', iconColor: '#f59e0b' },
    { label: 'Manage Role', icon: ShieldCheck, iconBg: '#f0fdf4', iconColor: '#22c55e' },
    { label: 'Export Data', icon: Download, iconBg: '#faf5ff', iconColor: '#a855f7' },
  ];

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-col gap-0.5">
        <h2 className="text-base font-semibold text-[#202939]">Quick Actions</h2>
        <p className="text-[13px] text-[#697586]">Frequently used administrative functions</p>
      </div>
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
        {actions.map(({ label, icon: Icon, iconBg, iconColor }) => (
          <button
            key={label}
            className="flex flex-row items-center gap-3 h-[80px] px-4 rounded-[10px] bg-white border border-[#e3e8ef] hover:border-[#a38654] hover:shadow-sm transition-all cursor-pointer"
          >
            <div
              className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: iconBg }}
            >
              <Icon className="h-4 w-4 flex-shrink-0" style={{ color: iconColor }} />
            </div>
            <span className="text-[14px] font-medium text-[#202939] text-left">{label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Stat Cards Row ────────────────────────────────────────────────────────────
function StatCardsRow() {
  const stats = [
    {
      label: 'Total Departments',
      value: '45',
      trend: '+38% vs last month',
      icon: Building,
      iconBg: '#fffbeb',
      iconColor: '#f59e0b',
    },
    {
      label: 'Teachers',
      value: '40',
      trend: '+56% vs last month',
      icon: GraduationCap,
      iconBg: '#eff6ff',
      iconColor: '#3b82f6',
    },
    {
      label: 'Students Enrolled',
      value: '143,445',
      trend: '+85% vs last month',
      icon: Users,
      iconBg: '#f0fdf4',
      iconColor: '#22c55e',
    },
    {
      label: 'Total Subjects',
      value: '32',
      trend: '+44% vs last month',
      icon: BookOpen,
      iconBg: '#faf5ff',
      iconColor: '#a855f7',
    },
  ];

  return (
    <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
      {stats.map(({ label, value, trend, icon: Icon, iconBg, iconColor }) => (
        <div
          key={label}
          className="h-[100px] p-4 rounded-[10px] bg-white border border-[#e3e8ef] flex flex-col gap-1"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div
                className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{ backgroundColor: iconBg }}
              >
                <Icon className="h-4 w-4" style={{ color: iconColor }} />
              </div>
              <span className="text-[13px] text-[#697586]">{label}</span>
            </div>
            <ChevronRight className="h-4 w-4 text-[#697586] flex-shrink-0" />
          </div>
          <p className="text-[28px] leading-none font-bold text-[#202939]">{value}</p>
          <div className="flex items-center gap-1">
            <TrendingUp className="h-3 w-3 text-[#2fc475]" />
            <span className="text-[12px] text-[#2fc475]">{trend}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Health + Insights Row (3fr : 2fr) ────────────────────────────────────────
function HealthAndInsightsRow() {
  const metrics = [
    { label: 'Attendance:', value: '88%', dotColor: '#22c55e' },
    { label: 'Academic consistency:', value: '7%', dotColor: '#e37a72' },
    { label: 'Teacher workload balance:', value: '75%', dotColor: '#f59e0b' },
    { label: 'Policy compliance:', value: '92%', dotColor: '#22c55e' },
  ];

  const insights = [
    '3 classes at academic risk',
    '1 teacher grading anomaly detected',
    'Attendance drop linked to timetable change',
  ];

  // Segmented progress bar: 30 small square segments (matches Figma)
  const totalSegments = 30;
  const filledSegments = Math.round((82 / 100) * totalSegments);

  return (
    <div className="grid gap-3" style={{ gridTemplateColumns: '3fr 2fr' }}>
      {/* School Health Index */}
      <div className="p-4 rounded-[10px] bg-white border border-[#e3e8ef] flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-[#fff1f0] flex items-center justify-center">
              <Activity className="h-4 w-4 text-[#f87171]" />
            </div>
            <span className="text-[15px] font-semibold text-[#202939]">School Health Index</span>
          </div>
          <ChevronRight className="h-4 w-4 text-[#697586]" />
        </div>

        <div className="flex items-baseline gap-2">
          <span className="text-[32px] font-bold leading-none text-[#202939]">82</span>
          <span className="text-base text-[#697586]">/ 100</span>
          <div className="flex items-center gap-1 ml-1">
            <TrendingUp className="h-3.5 w-3.5 text-[#2fc475]" />
            <span className="text-[13px] text-[#2fc475]">+34% vs last month</span>
          </div>
        </div>

        {/* Segmented progress bar — 30 small square segments (Figma style) */}
        <div className="flex gap-[3px] w-full h-[10px]" role="progressbar" aria-valuenow={82} aria-valuemin={0} aria-valuemax={100}>
          {Array.from({ length: totalSegments }).map((_, i) => (
            <div
              key={i}
              className="flex-1 rounded-[2px]"
              style={{ backgroundColor: i < filledSegments ? '#22c55e' : '#e5e7eb' }}
            />
          ))}
        </div>

        {/* Metrics 2x2 grid */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-2">
          {metrics.map(({ label, value, dotColor }) => (
            <div key={label} className="flex items-center gap-1.5">
              <span
                className="w-2 h-2 rounded-sm flex-shrink-0"
                style={{ backgroundColor: dotColor }}
              />
              <span className="text-[12px] text-[#697586] flex-1 min-w-0">{label}</span>
              <span className="text-[12px] font-semibold text-[#202939]">{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Intelligence Insights */}
      <div className="p-4 rounded-[10px] bg-white border border-[#e3e8ef] flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-[#faf5ff] flex items-center justify-center">
              <Brain className="h-4 w-4 text-[#a855f7]" />
            </div>
            <span className="text-[15px] font-semibold text-[#202939]">Intelligence Insights (Today)</span>
          </div>
          <ChevronRight className="h-4 w-4 text-[#697586]" />
        </div>

        <div className="flex flex-col gap-[10px]">
          {insights.map((text) => (
            <p key={text} className="text-[13px] text-[#202939]">{text}</p>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Status Cards Row (4 equal columns) ───────────────────────────────────────
function StatusCardsRow() {
  return (
    <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
      {/* Compliance Status */}
      <div className="h-[120px] p-4 rounded-[10px] bg-white border border-[#e3e8ef] flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-[#fffbeb] flex items-center justify-center">
              <ShieldCheck className="h-4 w-4 text-[#f59e0b]" />
            </div>
            <span className="text-[13px] text-[#697586]">Compliance Status</span>
          </div>
          <ChevronRight className="h-4 w-4 text-[#697586]" />
        </div>
        <div className="flex items-baseline gap-1">
          <span className="text-[28px] font-bold leading-none text-[#22c55e]">0</span>
          <span className="text-base text-[#202939]">critical violations</span>
        </div>
        <p className="text-[12px] text-[#697586]">2 grade overrides pending review</p>
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#e37a72]" />
          <span className="text-[12px] text-[#697586]">Last audit: 3 days ago</span>
        </div>
      </div>

      {/* Interventions — TWO side-by-side large numbers */}
      <div className="h-[120px] p-4 rounded-[10px] bg-white border border-[#e3e8ef] flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-[#eff6ff] flex items-center justify-center">
              <Activity className="h-4 w-4 text-[#3b82f6]" />
            </div>
            <span className="text-[13px] text-[#697586]">Interventions</span>
          </div>
          <ChevronRight className="h-4 w-4 text-[#697586]" />
        </div>
        {/* Two large numbers side-by-side */}
        <div className="flex flex-row gap-5 items-start">
          <div className="flex flex-col">
            <span className="text-[28px] font-bold leading-none text-[#202939]">6</span>
            <span className="text-[12px] text-[#697586]">Pending</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[28px] font-bold leading-none text-[#202939]">2</span>
            <span className="text-[12px] text-[#697586]">Active</span>
          </div>
        </div>
        <p className="text-[12px] text-[#697586]">Avg resolution time: 4.2 days</p>
      </div>

      {/* Interventions Completed */}
      <div className="h-[120px] p-4 rounded-[10px] bg-white border border-[#e3e8ef] flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-[#f0fdf4] flex items-center justify-center">
              <Activity className="h-4 w-4 text-[#22c55e]" />
            </div>
            <span className="text-[13px] text-[#697586]">Interventions</span>
          </div>
          <ChevronRight className="h-4 w-4 text-[#697586]" />
        </div>
        <div className="flex flex-col">
          <span className="text-[28px] font-bold leading-none text-[#202939]">2</span>
          <span className="text-[12px] text-[#697586]">Completed</span>
        </div>
      </div>

      {/* Students at Risk */}
      <div className="h-[120px] p-4 rounded-[10px] bg-white border border-[#e3e8ef] flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-[#fef2f2] flex items-center justify-center">
              <AlertTriangle className="h-4 w-4 text-[#e37a72]" />
            </div>
            <span className="text-[13px] text-[#697586]">Students at Risk</span>
          </div>
          <ChevronRight className="h-4 w-4 text-[#697586]" />
        </div>
        <div className="flex flex-col">
          <span className="text-[28px] font-bold leading-none text-[#202939]">2</span>
          <span className="text-[12px] text-[#697586]">Out of 620 students (7.7%)</span>
        </div>
        <div className="flex items-center gap-1">
          <TrendingUp className="h-3 w-3 text-[#2fc475]" />
          <span className="text-[12px] text-[#2fc475]">+5% since last week</span>
        </div>
      </div>
    </div>
  );
}

// ─── Bottom Panels Row (3fr : 2fr) ─────────────────────────────────────────────
function BottomPanelsRow() {
  const absenteesRows = [
    { grade: '10A', subject: 'Mathematics', teacher: 'Fatima Al-Mansour', absenteeism: '+12%', aboveThreshold: false },
    { grade: '10B', subject: 'Science', teacher: 'Ahmed Al-Sabah', absenteeism: '+26%', aboveThreshold: true },
    { grade: '10C', subject: 'Literature', teacher: 'Laila Al-Fahad', absenteeism: '+8%', aboveThreshold: false },
    { grade: '10D', subject: 'History', teacher: 'Mansour Al-Dtalib', absenteeism: '+76%', aboveThreshold: true },
    { grade: '10E', subject: 'Art', teacher: 'Sara Al-Jasem', absenteeism: '+35%', aboveThreshold: true },
  ];

  const barData = [
    { label: 'Students', primary: 38000, secondary: 42000 },
    { label: 'Teachers', primary: 8000, secondary: 10000 },
    { label: 'School Admins', primary: 5000, secondary: 6000 },
    { label: 'Parents', primary: 38000, secondary: 42000 },
    { label: 'Staff', primary: 12000, secondary: 15000 },
    { label: 'Super Admins', primary: 2000, secondary: 3000 },
  ];

  const maxBarValue = 42000;

  return (
    <div className="grid gap-3" style={{ gridTemplateColumns: '3fr 2fr' }}>
      {/* Absentees Alerts Panel */}
      <div className="p-4 rounded-[10px] bg-white border border-[#e3e8ef] flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <span className="text-[15px] font-semibold text-[#202939]">Absentees Alerts</span>
          <button className="text-[13px] font-medium text-[#a38654] cursor-pointer hover:underline">
            View All
          </button>
        </div>
        <p className="text-[12px] text-[#697586] -mt-1">
          Students who exceeded absenteeism threshold today
        </p>

        {/* Table */}
        <table className="w-full text-left border-collapse">
          <thead>
            <tr>
              {['Grade', 'Subject Name', 'Teacher', 'Absenteeism'].map((col) => (
                <th key={col} className="pb-2 text-[12px] font-medium text-[#697586]">
                  <div className="flex items-center gap-1">
                    {col}
                    <ArrowUpDown className="h-3 w-3 text-[#697586]" />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {absenteesRows.map(({ grade, subject, teacher, absenteeism, aboveThreshold }) => (
              <tr key={grade} className="border-t border-[#f1f5f9]">
                <td className="py-2.5 text-[13px] text-[#202939]">{grade}</td>
                <td className="py-2.5 text-[13px] text-[#202939]">{subject}</td>
                <td className="py-2.5 text-[13px] text-[#202939]">{teacher}</td>
                <td
                  className="py-2.5 text-[13px] font-medium"
                  style={{ color: aboveThreshold ? '#e37a72' : '#697586' }}
                >
                  {absenteeism}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* User Distribution by Role Panel */}
      <div className="p-4 rounded-[10px] bg-white border border-[#e3e8ef] flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <span className="text-[15px] font-semibold text-[#202939]">User Distribution by Role</span>
          <button className="text-[13px] font-medium text-[#a38654] cursor-pointer hover:underline">
            Manage Users
          </button>
        </div>
        <p className="text-[12px] text-[#697586] -mt-1">Platform user breakdown</p>

        {/* Simple bar chart — inline implementation (no recharts needed for layout) */}
        <div className="flex items-end gap-2 flex-1" style={{ height: 160 }}>
          {barData.map(({ label, primary, secondary }) => (
            <div key={label} className="flex flex-col items-center gap-1 flex-1">
              <div className="flex items-end gap-0.5 w-full" style={{ height: 130 }}>
                <div
                  className="flex-1 rounded-t-sm"
                  style={{
                    height: `${(primary / maxBarValue) * 100}%`,
                    backgroundColor: '#c4aa80',
                  }}
                />
                <div
                  className="flex-1 rounded-t-sm"
                  style={{
                    height: `${(secondary / maxBarValue) * 100}%`,
                    backgroundColor: '#e8dfc8',
                  }}
                />
              </div>
              <span className="text-[9px] text-[#697586] text-center leading-tight">{label}</span>
            </div>
          ))}
        </div>

        {/* Chart footer */}
        <div className="flex items-center justify-between">
          <span className="text-[12px] text-[#697586]">Highest position: Parents</span>
          <span className="text-[12px] font-semibold text-[#202939]">38000 / 42000</span>
        </div>
      </div>
    </div>
  );
}

// ─── DashboardBody ────────────────────────────────────────────────────────────
export default function DashboardBody() {
  return (
    <main className="flex-1 overflow-y-auto bg-[#f8fafc]">
      <div className="p-6 flex flex-col gap-4">
        {/* Section 1: Quick Actions */}
        <QuickActionsSection />

        {/* Section 2: 4-card stat row */}
        <StatCardsRow />

        {/* Section 3: Health Index (3fr) + Intelligence Insights (2fr) */}
        <HealthAndInsightsRow />

        {/* Section 4: 4-card status row */}
        <StatusCardsRow />

        {/* Section 5: Absentees (3fr) + User Distribution (2fr) */}
        <BottomPanelsRow />
      </div>
    </main>
  );
}
