import { useState } from 'react';
import Sidebar from '../components/dashboard/Sidebar';
import Navbar from '../components/dashboard/Navbar';
import DashboardBody from '../components/dashboard/DashboardBody';

export default function DashboardPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-[#f8fafc]">
      {/* Sidebar — hidden on mobile unless toggled, always visible on md+ */}
      <div className="hidden md:flex">
        <Sidebar isOpen={true} onClose={() => undefined} />
      </div>

      {/* Mobile sidebar — rendered in portal-like overlay */}
      <div className="md:hidden">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      </div>

      {/* Main area */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen((prev) => !prev)} />
        <DashboardBody />
      </div>
    </div>
  );
}
