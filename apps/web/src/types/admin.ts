export type UserRole = 'student' | 'instructor' | 'admin';

export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface PaginatedUsersResponse {
  items: AdminUser[];
  total: number;
  page: number;
  page_size: number;
}

export interface UpdateRolePayload {
  role: UserRole;
}

export interface UpdateStatusPayload {
  is_active: boolean;
}
