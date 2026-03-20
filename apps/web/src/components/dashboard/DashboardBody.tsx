import {
  UserPlus,
  Building2,
  ShieldCheck,
  FileDown,
  Building,
  Presentation,
  GraduationCap,
  BookOpen,
  ArrowRight,
  TrendingUp,
  Activity,
  AlertTriangle,
  ArrowUpDown,
  Brain,
} from 'lucide-react';

// ─── Quick Actions ─────────────────────────────────────────────────────────────
// UISpec: outer white card 1156x160, p-4, gap-4, rounded-xl
// Buttons: 263x56, bg-[#faf8f5] border-[#f6f3ef], rounded-xl, px-5 py-4, gap-3
// Label: 16px font-semibold; Icon: 24x24 (no badge wrapper)
function QuickActionsSection() {
  const actions = [
    { label: 'Add User',        icon: UserPlus,   iconColor: '#0ba5ec' },
    { label: 'New Institution', icon: Building2,  iconColor: '#a38654' },
    { label: 'Manage Role',     icon: ShieldCheck, iconColor: '#2fc475' },
    { label: 'Export Data',     icon: FileDown,   iconColor: '#9b8afb' },
  ];

  return (
    <div data-component="quick-actions" className="w-[1156px] bg-white rounded-xl border border-[#e3e8ef] p-4 flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h2 className="text-[24px] font-semibold leading-[28px] text-[#202939]">Quick Actions</h2>
        <p className="text-[16px] leading-[24px] text-[#697586]">Frequently used administrative functions</p>
      </div>
      <div className="flex flex-row gap-6">
        {actions.map(({ label, icon: Icon, iconColor }) => (
          <button
            key={label}
            className="w-[263px] flex flex-row items-center gap-3 h-14 px-5 py-4 rounded-xl bg-[#faf8f5] border border-[#f6f3ef] hover:border-[#a38654] hover:shadow-sm transition-all cursor-pointer"
          >
            <Icon className="h-6 w-6 flex-shrink-0" style={{ color: iconColor }} />
            <span className="text-[16px] font-semibold text-[#202939] text-left">{label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Stat Cards Row ─────────────────────────────────────────────────────────────
// UISpec: flex-row gap-6 (24px), each card 271x144, p-4, gap-3, rounded-xl
// Icon badge: 32x32 rounded-lg p-1, SOLID accent color bg, white icon 20x20
// Expand badge: 32x32 bg-[#a38654] rounded-lg, ArrowRight icon #202939
function StatCardsRow() {
  const stats = [
    { label: 'Total Departments', value: '45',     trend: '+ 38%', trendLabel: 'vs last month', icon: Building,     iconBg: '#a38654' },
    { label: 'Teachers',          value: '40',     trend: '+ 56%', trendLabel: 'vs last month', icon: Presentation, iconBg: '#2fc475' },
    { label: 'Students Enrolled', value: '143,445',trend: '88%',   trendLabel: 'vs last month', icon: GraduationCap,iconBg: '#0ba5ec' },
    { label: 'Total Subjects',    value: '32',     trend: '+ 44%', trendLabel: 'vs last month', icon: BookOpen,     iconBg: '#9b8afb' },
  ];

  return (
    <div data-component="stat-cards" className="flex flex-row gap-6">
      {stats.map(({ label, value, trend, trendLabel, icon: Icon, iconBg }) => (
        <div key={label} className="w-[271px] flex-shrink-0 h-[144px] p-4 rounded-xl bg-white border border-[#e3e8ef] flex flex-col gap-3">
          {/* Row 1: icon badge + label + expand arrow */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg p-1 flex items-center justify-center flex-shrink-0" style={{ backgroundColor: iconBg }}>
                <Icon className="h-5 w-5 text-white" />
              </div>
              <span className="text-[14px] text-[#697586]">{label}</span>
            </div>
            <div className="w-8 h-8 rounded-lg bg-[#a38654] flex items-center justify-center flex-shrink-0">
              <ArrowRight className="h-[18px] w-[18px] text-[#202939]" />
            </div>
          </div>
          {/* Row 2: stat value — UISpec: lineHeightPx 32 */}
          <p className="text-[32px] leading-[32px] font-semibold text-[#202939]">{value}</p>
          {/* Row 3: trend */}
          <div className="flex items-center gap-1">
            <TrendingUp className="h-3 w-3 text-[#2fc475] flex-shrink-0" />
            <span className="text-[12px] font-semibold text-[#2fc475]">{trend}</span>
            <span className="text-[12px] text-[#697586]">{trendLabel}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── School Health + Intelligence Insights Row ─────────────────────────────────
// UISpec: flex-row gap-6, both cards 566x232, p-4, rounded-xl
// Progress bar: 40 discrete segments (8x12px, r=2, gap=6px): 31 green + 9 gold
// Insights: each item 534x44 bg-[#f8fafc] rounded-lg px-4, text-[18px] font-medium
function HealthAndInsightsRow() {
  const metrics = [
    { label: 'Attendance:',              value: '88%', dotColor: '#2fc475' },
    { label: 'Academic consistency:',    value: '7%',  dotColor: '#c4392f' },
    { label: 'Teacher workload balance:',value: '75%', dotColor: '#c47f2f' },
    { label: 'Policy compliance:',       value: '92%', dotColor: '#2fc475' },
  ];

  const insights = [
    '3 classes at academic risk',
    '1 teacher grading anomaly detected',
    'Attendance drop linked to timetable change',
  ];

  const TOTAL_SEGMENTS = 40;
  const GREEN_SEGMENTS = 31;

  return (
    <div className="flex flex-row gap-6">
      {/* School Health Index — 566x232 per UISpec */}
      <div data-component="school-health" className="w-[566px] flex-shrink-0 rounded-xl bg-white border border-[#e3e8ef] p-4 flex flex-col gap-4">
        {/* Title row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#e37a73] flex items-center justify-center flex-shrink-0">
              <Activity className="h-5 w-5 text-white" />
            </div>
            <span className="text-[16px] font-normal text-[#697586]">School Health Index</span>
          </div>
          <div className="w-8 h-8 rounded-lg bg-[#a38654] flex items-center justify-center flex-shrink-0">
            <ArrowRight className="h-[18px] w-[18px] text-[#202939]" />
          </div>
        </div>

        {/* Score + trend — "82 / 100" as single text (32px) */}
        <div className="flex items-center gap-3">
          <span className="text-[32px] font-semibold leading-[32px] text-[#202939]">82 / 100</span>
          <div className="flex items-center gap-1">
            <span className="text-[16px] font-semibold text-[#2fc475]">+ 34%</span>
            <span className="text-[16px] text-[#697586]">vs last month</span>
          </div>
        </div>

        {/* 40 discrete segments: 8x12px each, gap-[6px], 31 green + 9 gold */}
        <div className="flex gap-[6px]" role="progressbar" aria-valuenow={82} aria-valuemin={0} aria-valuemax={100}>
          {Array.from({ length: TOTAL_SEGMENTS }).map((_, i) => (
            <div
              key={i}
              className="w-[8px] h-[12px] rounded-[2px] flex-shrink-0"
              style={{ backgroundColor: i < GREEN_SEGMENTS ? '#2fc475' : '#a38654' }}
            />
          ))}
        </div>

        {/* Metrics legend: 2-col grid (Figma: 76px tall, 2 rows × 2 cols) */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-2">
          {metrics.map(({ label, value, dotColor }) => (
            <div key={label} className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-[2px] flex-shrink-0" style={{ backgroundColor: dotColor }} />
              <span className="text-[12px] text-[#697586] flex-1 min-w-0">{label}</span>
              <span className="text-[12px] font-semibold text-[#202939]">{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Intelligence Insights — 566x232 per UISpec */}
      <div data-component="intelligence-insights" className="w-[566px] flex-shrink-0 rounded-xl bg-white border border-[#e3e8ef] p-4 flex flex-col gap-3">
        {/* Title row: AI badge is 24x24 r=4 (NOT 32x32 r=8 like other cards) */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-[#9b8afb] flex items-center justify-center flex-shrink-0">
              <Brain className="h-3.5 w-3.5 text-white" />
            </div>
            <span className="text-[16px] font-normal text-[#697586]">Intelligence Insights (Today)</span>
          </div>
          <div className="w-8 h-8 rounded-lg bg-[#a38654] flex items-center justify-center flex-shrink-0">
            <ArrowRight className="h-[18px] w-[18px] text-[#202939]" />
          </div>
        </div>

        {/* Insight items: pill-cards 44px tall, bg-[#f8fafc] rounded-lg px-4, text-[18px] font-medium */}
        <div className="flex flex-col gap-3">
          {insights.map((text) => (
            <div key={text} className="h-[44px] bg-[#f8fafc] rounded-lg px-4 flex items-center flex-shrink-0">
              <p className="text-[18px] font-medium text-[#202939]">{text}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Status Cards Row (3 cards) ────────────────────────────────────────────────
// UISpec: flex-row gap-6, 3 cards (Compliance, Interventions, Students at Risk)
// Each card ~369px wide (flex-1), h-[172px], p-4, rounded-xl
// Interventions card has 3 side-by-side metrics (Pending=6, Active=2, Completed=2)
function StatusCardsRow() {
  return (
    <div data-component="status-cards" className="flex flex-row gap-6">
      {/* Compliance Status — 369px per UISpec */}
      <div className="w-[369px] flex-shrink-0 h-[172px] p-4 rounded-xl bg-white border border-[#e3e8ef] flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#a38654] flex items-center justify-center flex-shrink-0">
              <ShieldCheck className="h-5 w-5 text-white" />
            </div>
            <span className="text-[14px] text-[#697586]">Compliance Status</span>
          </div>
          <div className="w-8 h-8 rounded-lg bg-[#a38654] flex items-center justify-center flex-shrink-0">
            <ArrowRight className="h-[18px] w-[18px] text-[#202939]" />
          </div>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-[32px] font-semibold leading-[32px] text-[#202939]">0</span>
          <span className="text-[16px] text-[#202939]">critical violations</span>
        </div>
        <p className="text-[14px] text-[#697586]">2 grade overrides pending review</p>
        <div className="flex items-center gap-1">
          <span className="text-[14px] text-[#697586]">Last audit:</span>
          <span className="text-[14px] font-semibold text-[#2fc475]">3 days ago</span>
        </div>
      </div>

      {/* Interventions — 369px per UISpec */}
      <div className="w-[369px] flex-shrink-0 h-[172px] p-4 rounded-xl bg-white border border-[#e3e8ef] flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#f7f5ef] flex items-center justify-center flex-shrink-0">
              <Activity className="h-5 w-5 text-[#a38654]" />
            </div>
            <span className="text-[14px] text-[#697586]">Interventions</span>
          </div>
          <div className="w-8 h-8 rounded-lg bg-[#a38654] flex items-center justify-center flex-shrink-0">
            <ArrowRight className="h-[18px] w-[18px] text-[#202939]" />
          </div>
        </div>
        {/* 3 metrics side by side */}
        <div className="flex flex-row gap-4">
          {[
            { value: '6', label: 'Pending' },
            { value: '2', label: 'Active' },
            { value: '2', label: 'Completed' },
          ].map(({ value, label }) => (
            <div key={label} className="flex flex-col">
              <span className="text-[32px] font-semibold leading-[32px] text-[#202939]">{value}</span>
              <span className="text-[12px] text-[#697586]">{label}</span>
            </div>
          ))}
        </div>
        <p className="text-[12px] text-[#697586]">
          Avg resolution time: <span className="font-semibold text-[#2fc475]">4.2 days</span>
        </p>
      </div>

      {/* Students at Risk — 369px per UISpec */}
      <div className="w-[369px] flex-shrink-0 h-[180px] p-4 rounded-xl bg-white border border-[#e3e8ef] flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-[#f7f5ef] flex items-center justify-center flex-shrink-0">
              <AlertTriangle className="h-5 w-5 text-[#a38654]" />
            </div>
            <span className="text-[14px] text-[#697586]">Students at Risk</span>
          </div>
          <div className="w-8 h-8 rounded-lg bg-[#a38654] flex items-center justify-center flex-shrink-0">
            <ArrowRight className="h-[18px] w-[18px] text-[#202939]" />
          </div>
        </div>
        <div className="flex flex-col">
          <span className="text-[32px] font-semibold leading-[32px] text-[#202939]">2</span>
          <span className="text-[12px] text-[#697586]">Out of 620 students (7.7%)</span>
        </div>
        <div className="flex items-center gap-1">
          <TrendingUp className="h-3 w-3 text-[#2fc475] flex-shrink-0" />
          <span className="text-[12px] font-semibold text-[#2fc475]">+5%</span>
          <span className="text-[12px] text-[#697586]">since last week</span>
        </div>
      </div>
    </div>
  );
}

// ─── Bottom Row ─────────────────────────────────────────────────────────────────
// Absentees: 566x400, no outer padding — header has p-4, table rows h-[52px]
// Column widths from Figma: Grade=100, Subject=152, Teacher=162, Absenteeism=152
// Absenteeism values: red ▲ triangle + value in #c4392f
// User Distribution: 566x400, bars are exact pixel heights from Figma node data
function BottomPanelsRow() {
  const absenteesRows = [
    { grade: '10A', subject: 'Mathematics', teacher: 'Fatima Al-Mansour',  absenteeism: '12%' },
    { grade: '10B', subject: 'Science',     teacher: 'Ahmed Al-Sabah',     absenteeism: '28%' },
    { grade: '10C', subject: 'Literature',  teacher: 'Laila Al-Fahad',     absenteeism: '8%'  },
    { grade: '10D', subject: 'History',     teacher: 'Mansour Al-Otaibi',  absenteeism: '76%' },
    { grade: '10E', subject: 'Art',         teacher: 'Sara Al-Jasem',      absenteeism: '35%' },
  ];

  const tableColumns = [
    { label: 'Grade',        width: 100 },
    { label: 'Subject Name', width: 152 },
    { label: 'Teacher',      width: 162 },
    { label: 'Absenteeism',  width: 152 },
  ];

  // Exact pixel heights from Figma node data (1:10844 children)
  const bars = [
    { label: 'Students',     outerH: 170, innerH: 104 },
    { label: 'Teachers',     outerH: 104, innerH: 59  },
    { label: 'School Admins',outerH: 59,  innerH: 24  },
    { label: 'Parents',      outerH: 210, innerH: 139 },
    { label: 'Staff',        outerH: 121, innerH: 63  },
    { label: 'Super Admins', outerH: 45,  innerH: 21  },
  ];

  const yLabels = ['42000', '36000', '30000', '24000', '18000', '12000', '6000', '0'];

  return (
    <div className="flex flex-row gap-6">
      {/* Absentees Alerts — 566px wide per UISpec, no outer padding; children have own padding */}
      <div data-component="absentees-table" className="w-[566px] flex-shrink-0 rounded-xl bg-white border border-[#e3e8ef] flex flex-col overflow-hidden">
        {/* Card header: p-4, flex-row justify-between */}
        <div className="flex items-start justify-between p-4 gap-4">
          <div className="flex flex-col gap-1">
            <h3 className="text-[24px] font-semibold leading-[28px] text-[#202939]">Absenties Alerts</h3>
            <p className="text-[16px] leading-[24px] text-[#697586]">Students who exceeded absenteeism threshold today</p>
          </div>
          <button className="text-[16px] font-medium text-[#697586] hover:text-[#a38654] transition-colors whitespace-nowrap mt-1 cursor-pointer">
            View All
          </button>
        </div>

        {/* Table */}
        <div className="flex flex-col">
          {/* Header row: bg-[#f8fafc], h-[52px], px-4 */}
          <div className="flex bg-[#f8fafc] border-b border-[#e3e8ef]">
            {tableColumns.map(({ label, width }) => (
              <div
                key={label}
                className="h-[52px] flex items-center gap-1 px-4 text-[14px] font-semibold text-[#202939] flex-shrink-0"
                style={{ width }}
              >
                {label}
                <ArrowUpDown className="h-3 w-3 text-[#c0ad81] flex-shrink-0" />
              </div>
            ))}
          </div>

          {/* Data rows: h-[52px], border-bottom #e3e8ef */}
          {absenteesRows.map(({ grade, subject, teacher, absenteeism }) => (
            <div key={grade} className="flex border-b border-[#e3e8ef] last:border-b-0">
              <div className="h-[52px] flex items-center px-4 text-[12px] font-medium text-[#202939] flex-shrink-0" style={{ width: 100 }}>{grade}</div>
              <div className="h-[52px] flex items-center px-4 text-[12px] font-medium text-[#202939] flex-shrink-0" style={{ width: 152 }}>{subject}</div>
              <div className="h-[52px] flex items-center px-4 text-[12px] font-medium text-[#202939] flex-shrink-0" style={{ width: 162 }}>{teacher}</div>
              {/* Absenteeism: red upward triangle + value */}
              <div className="h-[52px] flex items-center gap-1 px-4 flex-shrink-0" style={{ width: 152 }}>
                <span className="text-[10px] text-[#c4392f] leading-none">▲</span>
                <span className="text-[14px] text-[#c4392f]">{absenteeism}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* User Distribution by Role — 566px wide per UISpec */}
      <div data-component="user-distribution" className="w-[566px] flex-shrink-0 rounded-xl bg-white border border-[#e3e8ef] p-4 flex flex-col gap-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex flex-col gap-1">
            <h3 className="text-[24px] font-semibold leading-[28px] text-[#202939]">User Distribution by Role</h3>
            <p className="text-[16px] leading-[24px] text-[#697586]">Platform user breakdown</p>
          </div>
          <button className="text-[16px] font-normal text-[#697586] hover:text-[#a38654] transition-colors whitespace-nowrap mt-1 cursor-pointer">
            Manage Users
          </button>
        </div>

        {/* Chart area: Y-axis (29px) + chart body (flex-1) */}
        <div className="flex flex-row gap-2" style={{ height: 244 }}>
          {/* Y-axis labels: 29px wide, 8 labels, justify-between, pb aligns "0" with bar bottom */}
          <div className="flex flex-col justify-between flex-shrink-0 pb-[26px]" style={{ width: 29, height: 244 }}>
            {yLabels.map((v) => (
              <span key={v} className="text-[10px] text-[#202939] text-right leading-[14px] block">{v}</span>
            ))}
          </div>

          {/* Chart body: bars (218px) + gap-3 + x-labels (14px) */}
          <div className="flex-1 flex flex-col gap-3">
            {/* Bars container: 218px, bottom-aligned, gap-8 (32px) */}
            <div className="flex flex-row items-end justify-center gap-8" style={{ height: 218 }}>
              {bars.map(({ label, outerH, innerH }) => (
                <div key={label} className="flex flex-col items-center">
                  {/* Outer = bg track; inner = gold fill, bottom-aligned via justify-end */}
                  <div
                    className="w-12 rounded flex flex-col justify-end bg-[#fbfaf7]"
                    style={{ height: outerH }}
                  >
                    <div className="w-12 rounded bg-[#a38654]" style={{ height: innerH }} />
                  </div>
                </div>
              ))}
            </div>

            {/* X-axis labels: Inter 10px, each 48px (w-12) centered under bar, gap-8 */}
            <div className="flex flex-row items-center justify-center gap-8">
              {bars.map(({ label }) => (
                <div key={label} className="w-12 text-center flex-shrink-0">
                  <span className="text-[10px] text-[#202939] leading-[14px]">{label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between">
          <span className="text-[14px] text-[#202939]">Highest position: Parents</span>
          <span className="text-[14px] text-[#202939]">38000 / 42000</span>
        </div>
      </div>
    </div>
  );
}

// ─── DashboardBody ─────────────────────────────────────────────────────────────
// UISpec: p-6 (24px), gap-6 (24px) — matches Figma body padding + row gaps
export default function DashboardBody() {
  return (
    <main className="flex-1 overflow-y-auto bg-[#f8fafc]">
      <div className="p-6 flex flex-col gap-6">
        <QuickActionsSection />
        <StatCardsRow />
        <HealthAndInsightsRow />
        <StatusCardsRow />
        <BottomPanelsRow />
      </div>
    </main>
  );
}
