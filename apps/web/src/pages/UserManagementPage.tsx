import { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import Sidebar from '../components/dashboard/Sidebar';
import Navbar from '../components/dashboard/Navbar';
import api from '../lib/api';
import { useAuthStore } from '../lib/auth-store';
import {
  useAdminUsers,
  useUpdateUserRole,
  useUpdateUserStatus,
} from '../hooks/useAdminUsers';
import type { AdminUser, UserRole } from '../types/admin';

// ─── Role & Status Color Tokens ────────────────────────────────────────────────

const ROLE_COLORS: Record<
  UserRole,
  { bg: string; text: string; dot: string }
> = {
  student: { bg: '#eff8ff', text: '#2e90fa', dot: '#2e90fa' },
  instructor: { bg: '#edfcf2', text: '#16b364', dot: '#3ccb7f' },
  admin: { bg: '#fffaeb', text: '#f79009', dot: '#fdb022' },
};

// ─── Admin Guard: fetch /users/me including role ───────────────────────────────

interface CurrentUserWithRole {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

function useCurrentUserWithRole() {
  const accessToken = useAuthStore((s) => s.accessToken);

  return useQuery<CurrentUserWithRole>({
    queryKey: ['currentUserWithRole'],
    queryFn: async () => {
      const { data } = await api.get<CurrentUserWithRole>('/users/me');
      return data;
    },
    enabled: !!accessToken,
    staleTime: 1000 * 60 * 5,
  });
}

// ─── Sub-components ────────────────────────────────────────────────────────────

function AvatarCircle({ fullName }: { fullName: string }) {
  const initials = fullName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div
      className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 text-white text-sm font-semibold"
      style={{ backgroundColor: '#a38654' }}
    >
      {initials}
    </div>
  );
}

function RoleBadge({ role }: { role: UserRole }) {
  const colors = ROLE_COLORS[role];
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold capitalize"
      style={{ backgroundColor: colors.bg, color: colors.text }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full flex-shrink-0"
        style={{ backgroundColor: colors.dot }}
      />
      {role}
    </span>
  );
}

function StatusBadge({ isActive }: { isActive: boolean }) {
  return isActive ? (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold"
      style={{
        backgroundColor: '#edfcf2',
        color: '#16b364',
        border: '1px solid #d3f8df',
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full flex-shrink-0"
        style={{ backgroundColor: '#3ccb7f' }}
      />
      Active
    </span>
  ) : (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold"
      style={{
        backgroundColor: '#fff1f3',
        color: '#f63d68',
        border: '1px solid #ffd5da',
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full flex-shrink-0"
        style={{ backgroundColor: '#f97066' }}
      />
      Inactive
    </span>
  );
}

interface UserRowProps {
  user: AdminUser;
  onRoleChange: (userId: string, role: UserRole) => void;
  onStatusToggle: (userId: string, isActive: boolean) => void;
  isUpdatingRole: boolean;
  isUpdatingStatus: boolean;
}

function UserRow({
  user,
  onRoleChange,
  onStatusToggle,
  isUpdatingRole,
  isUpdatingStatus,
}: UserRowProps) {
  const roleColors = ROLE_COLORS[user.role];

  return (
    <tr className="border-b border-[#e3e8ef] last:border-b-0 hover:bg-[#f8fafc] transition-colors">
      {/* Full Name + Avatar */}
      <td className="px-4 py-4">
        <div className="flex items-center gap-3">
          <AvatarCircle fullName={user.full_name} />
          <span className="text-sm font-medium text-[#202939] truncate max-w-[160px]">
            {user.full_name}
          </span>
        </div>
      </td>

      {/* Email */}
      <td className="px-4 py-4">
        <span className="text-sm text-[#697586] truncate max-w-[200px] block">
          {user.email}
        </span>
      </td>

      {/* Role — editable select */}
      <td className="px-4 py-4">
        <div className="relative inline-flex items-center">
          <span
            className="w-1.5 h-1.5 rounded-full absolute left-2.5 z-10 pointer-events-none"
            style={{ backgroundColor: roleColors.dot }}
          />
          <select
            value={user.role}
            disabled={isUpdatingRole}
            onChange={(e) => onRoleChange(user.id, e.target.value as UserRole)}
            className="pl-6 pr-3 py-1 rounded-full text-xs font-semibold appearance-none cursor-pointer border-0 outline-none focus:ring-1 focus:ring-[#a38654] disabled:opacity-60 disabled:cursor-not-allowed"
            style={{
              backgroundColor: roleColors.bg,
              color: roleColors.text,
            }}
          >
            <option value="student">student</option>
            <option value="instructor">instructor</option>
            <option value="admin">admin</option>
          </select>
        </div>
      </td>

      {/* Status badge */}
      <td className="px-4 py-4">
        <StatusBadge isActive={user.is_active} />
      </td>

      {/* Actions */}
      <td className="px-4 py-4">
        <button
          onClick={() => onStatusToggle(user.id, !user.is_active)}
          disabled={isUpdatingStatus}
          className="text-xs font-medium px-3 py-1.5 rounded-lg border border-[#e3e8ef] text-[#697586] hover:text-[#202939] hover:bg-[#f8fafc] transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {user.is_active ? 'Deactivate' : 'Activate'}
        </button>
      </td>
    </tr>
  );
}

function TableSkeleton() {
  return (
    <>
      {Array.from({ length: 5 }).map((_, i) => (
        <tr key={i} className="border-b border-[#e3e8ef] animate-pulse">
          <td className="px-4 py-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-[#e3e8ef]" />
              <div className="h-4 w-32 rounded bg-[#e3e8ef]" />
            </div>
          </td>
          <td className="px-4 py-4">
            <div className="h-4 w-44 rounded bg-[#e3e8ef]" />
          </td>
          <td className="px-4 py-4">
            <div className="h-5 w-20 rounded-full bg-[#e3e8ef]" />
          </td>
          <td className="px-4 py-4">
            <div className="h-5 w-16 rounded-full bg-[#e3e8ef]" />
          </td>
          <td className="px-4 py-4">
            <div className="h-7 w-20 rounded-lg bg-[#e3e8ef]" />
          </td>
        </tr>
      ))}
    </>
  );
}

// ─── Pagination ────────────────────────────────────────────────────────────────

interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (p: number) => void;
}

function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div className="flex items-center justify-center gap-1.5 px-4 py-4">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page === 1}
        className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium border border-[#e3e8ef] bg-white text-[#697586] hover:text-[#202939] hover:bg-[#f8fafc] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        <ChevronLeft className="h-4 w-4" />
        Previous
      </button>

      <div className="flex items-center gap-1">
        {pages.map((p) => (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            className="w-8 h-8 rounded-lg text-sm font-medium transition-colors"
            style={
              p === page
                ? { backgroundColor: '#f7f5ef', color: '#a38654' }
                : { color: '#697586' }
            }
          >
            {p}
          </button>
        ))}
      </div>

      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page === totalPages}
        className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium border border-[#e3e8ef] bg-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        style={{ color: '#a38654' }}
      >
        Next
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
}

// ─── Main Page Body ────────────────────────────────────────────────────────────

const PAGE_SIZE = 10;

function UserManagementBody() {
  const [searchInput, setSearchInput] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('All');
  const [page, setPage] = useState(1);

  // Debounce search input by 500 ms
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchInput);
      setPage(1);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // Reset page when role filter changes
  useEffect(() => {
    setPage(1);
  }, [roleFilter]);

  const { data, isLoading, isError, error } = useAdminUsers({
    search: debouncedSearch,
    role: roleFilter,
    page,
    pageSize: PAGE_SIZE,
  });

  const { mutate: updateRole, isPending: isUpdatingRole } = useUpdateUserRole();
  const { mutate: updateStatus, isPending: isUpdatingStatus } = useUpdateUserStatus();

  const handleRoleChange = (userId: string, role: UserRole) => {
    updateRole({ userId, payload: { role } });
  };

  const handleStatusToggle = (userId: string, isActive: boolean) => {
    updateStatus({ userId, payload: { is_active: isActive } });
  };

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  return (
    <main className="flex-1 overflow-y-auto p-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1
          className="font-semibold text-[#202939]"
          style={{ fontSize: '24px' }}
        >
          User Management
        </h1>
        <p
          className="mt-1 font-medium text-[#697586]"
          style={{ fontSize: '16px' }}
        >
          Manage platform users, roles, and account status
        </p>
      </div>

      {/* Search + Filter row */}
      <div className="flex flex-col sm:flex-row gap-3 mb-5">
        {/* Search input */}
        <div
          className="flex items-center gap-2 flex-1 px-3"
          style={{
            background: '#ffffff',
            border: '1px solid #e3e8ef',
            borderRadius: 8,
            height: 36,
          }}
        >
          <Search className="h-4 w-4 flex-shrink-0" style={{ color: '#202939' }} />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search users by name or email"
            className="flex-1 bg-transparent text-sm text-[#202939] placeholder-[#697586] outline-none min-w-0"
          />
        </div>

        {/* Role filter */}
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="px-3 text-sm outline-none cursor-pointer"
          style={{
            background: '#ffffff',
            border: '1px solid #e3e8ef',
            borderRadius: 8,
            height: 36,
            color: '#697586',
            fontSize: '14px',
            fontWeight: 600,
          }}
        >
          {['All', 'student', 'instructor', 'admin'].map((opt) => (
            <option key={opt} value={opt}>
              {opt.charAt(0).toUpperCase() + opt.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* Table container */}
      <div
        className="overflow-hidden"
        style={{
          background: '#fcfcfd',
          border: '1px solid #e3e8ef',
          borderRadius: 12,
        }}
      >
        {/* Error state */}
        {isError && (
          <div className="flex items-center justify-center py-16 text-sm text-[#f63d68]">
            {(error as Error)?.message ?? 'Failed to load users. Please try again.'}
          </div>
        )}

        {!isError && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[600px] border-collapse">
              <thead>
                <tr
                  style={{
                    backgroundColor: '#a38654',
                    height: 52,
                  }}
                >
                  {['Full Name', 'Email', 'Role', 'Status', 'Actions'].map((label) => (
                    <th
                      key={label}
                      className="px-4 text-left"
                      style={{
                        color: '#202939',
                        fontSize: '14px',
                        fontWeight: 600,
                      }}
                    >
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <TableSkeleton />
                ) : data && data.items.length > 0 ? (
                  data.items.map((user) => (
                    <UserRow
                      key={user.id}
                      user={user}
                      onRoleChange={handleRoleChange}
                      onStatusToggle={handleStatusToggle}
                      isUpdatingRole={isUpdatingRole}
                      isUpdatingStatus={isUpdatingStatus}
                    />
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-16">
                      <div className="flex flex-col items-center justify-center gap-1">
                        <p className="text-sm font-medium text-[#202939]">
                          No users found
                        </p>
                        <p className="text-sm text-[#697586]">
                          Try adjusting your search or filter criteria
                        </p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!isLoading && !isError && data && data.total > PAGE_SIZE && (
          <div className="border-t border-[#e3e8ef]">
            <Pagination
              page={page}
              totalPages={totalPages}
              onPageChange={setPage}
            />
          </div>
        )}
      </div>
    </main>
  );
}

// ─── Page Root ─────────────────────────────────────────────────────────────────

export default function UserManagementPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { data: currentUser, isLoading: isLoadingUser } = useCurrentUserWithRole();

  // Admin guard — wait until user data resolves
  if (!isLoadingUser && currentUser && currentUser.role !== 'admin') {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#f8fafc]">
      {/* Sidebar — always visible on md+, toggle on mobile */}
      <div className="hidden md:flex">
        <Sidebar isOpen={true} onClose={() => undefined} />
      </div>
      <div className="md:hidden">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      </div>

      {/* Main area */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Navbar onMenuClick={() => setSidebarOpen((prev) => !prev)} />
        {isLoadingUser ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-2 border-[#a38654] border-t-transparent rounded-full animate-spin" />
              <span className="text-sm text-[#697586]">Loading...</span>
            </div>
          </div>
        ) : (
          <UserManagementBody />
        )}
      </div>
    </div>
  );
}
