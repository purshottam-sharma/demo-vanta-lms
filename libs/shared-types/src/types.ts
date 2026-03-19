export interface ApiResponse<T> {
  data: T;
  message?: string;
  status?: number;
  ok?: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ErrorResponse {
  error: string;
  detail?: string;
  status: number;
}
