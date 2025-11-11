import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  User,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  UserUpdateRequest,
  TutorPerformanceData,
  TutorSessionsResponse,
  TutorRecommendationsResponse,
  TutorProfile,
  TutorProfileResponse,
  FeedbackTokenValidation,
  StudentFeedbackSubmission,
  FeedbackSubmissionResponse,
  RetentionScanResult,
  ArchivalRequest,
  ArchivalResult,
  AnonymizationRequest,
  AnonymizationResult,
  DeletionRequest,
  DeletionResult,
  RetentionReport,
  RetentionPolicy,
  RetentionStatusCheck
} from '@/lib/types';

// Create axios instance with default config
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Load token from localStorage on init (client-side only)
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('access_token');
      if (this.accessToken) {
        this.setAuthHeader(this.accessToken);
      }
    }

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.clearAuth();
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  private setAuthHeader(token: string) {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  private clearAuthHeader() {
    delete this.client.defaults.headers.common['Authorization'];
  }

  setToken(token: string) {
    this.accessToken = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
    }
    this.setAuthHeader(token);
  }

  clearAuth() {
    this.accessToken = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
    }
    this.clearAuthHeader();
  }

  getToken(): string | null {
    return this.accessToken;
  }

  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  // Auth endpoints
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    // FastAPI OAuth2 expects form data, not JSON
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await this.client.post<LoginResponse>(
      '/auth/jwt/login',
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );

    this.setToken(response.data.access_token);
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/auth/jwt/logout');
    } finally {
      this.clearAuth();
    }
  }

  async register(data: RegisterRequest): Promise<User> {
    const response = await this.client.post<User>('/auth/register', data);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/users/me');
    return response.data;
  }

  async updateCurrentUser(data: UserUpdateRequest): Promise<User> {
    const response = await this.client.patch<User>('/users/me', data);
    return response.data;
  }

  // User management endpoints (admin only)
  async getUsers(): Promise<User[]> {
    const response = await this.client.get<{ success: boolean; users: User[]; total: number; page: number; page_size: number; total_pages: number }>('/api/admin/users');
    return response.data.users;
  }

  async getUser(userId: number): Promise<User> {
    const response = await this.client.get<User>(`/users/${userId}`);
    return response.data;
  }

  async updateUser(userId: number, data: UserUpdateRequest): Promise<User> {
    const response = await this.client.patch<User>(`/users/${userId}`, data);
    return response.data;
  }

  async deleteUser(userId: number): Promise<void> {
    await this.client.delete(`/users/${userId}`);
  }

  async createUser(data: RegisterRequest): Promise<User> {
    // Uses the register endpoint but with admin privileges
    return this.register(data);
  }

  // Tutor Portal endpoints
  async getTutorMetrics(
    tutorId: string,
    window: '7day' | '30day' | '90day' = '30day'
  ): Promise<TutorPerformanceData> {
    const response = await this.client.get<TutorPerformanceData>(
      `/api/tutors/${tutorId}/metrics`,
      { params: { window } }
    );
    return response.data;
  }

  async getTutorSessions(
    tutorId: string,
    limit: number = 20,
    offset: number = 0
  ): Promise<TutorSessionsResponse> {
    const response = await this.client.get<TutorSessionsResponse>(
      `/api/tutors/${tutorId}/sessions`,
      { params: { limit, offset } }
    );
    return response.data;
  }

  async getTutorRecommendations(tutorId: string): Promise<TutorRecommendationsResponse> {
    const response = await this.client.get<TutorRecommendationsResponse>(
      `/api/tutors/${tutorId}/recommendations`
    );
    return response.data;
  }

  async getTutorFeedback(
    tutorId: string,
    limit: number = 20,
    offset: number = 0
  ): Promise<{ success: boolean; feedback: any[]; pagination: any }> {
    const response = await this.client.get(
      `/api/tutors/${tutorId}/feedback`,
      { params: { limit, offset } }
    );
    return response.data;
  }

  async getTutorProfile(tutorId: string): Promise<TutorProfile> {
    const response = await this.client.get<{
      success: boolean;
      tutor_id: string;
      name: string;
      email: string;
      onboarding_date: string;
      status: string;
      subjects: string[];
      education_level?: string;
      location?: string;
    }>(`/api/tutors/${tutorId}/profile`);

    return {
      tutor_id: response.data.tutor_id,
      name: response.data.name,
      email: response.data.email,
      onboarding_date: response.data.onboarding_date,
      status: response.data.status,
      subjects: response.data.subjects,
      education_level: response.data.education_level,
      location: response.data.location,
    };
  }

  // Tutor Profile endpoints (for managers)
  async getTutorProfileDetail(tutorId: string): Promise<TutorProfileResponse> {
    const response = await this.client.get<TutorProfileResponse>(
      `/api/tutor-profile/${tutorId}`
    );
    return response.data;
  }

  async createManagerNote(
    tutorId: string,
    noteText: string,
    isImportant: boolean,
    authorName: string
  ): Promise<{ success: boolean; note_id: string }> {
    const response = await this.client.post<{ success: boolean; note_id: string }>(
      `/api/tutor-profile/${tutorId}/notes`,
      {
        note_text: noteText,
        is_important: isImportant,
        author_name: authorName,
      }
    );
    return response.data;
  }

  async updateManagerNote(
    tutorId: string,
    noteId: string,
    noteText: string,
    isImportant: boolean
  ): Promise<{ success: boolean }> {
    const response = await this.client.put<{ success: boolean }>(
      `/api/tutor-profile/${tutorId}/notes/${noteId}`,
      {
        note_text: noteText,
        is_important: isImportant,
      }
    );
    return response.data;
  }

  async deleteManagerNote(tutorId: string, noteId: string): Promise<{ success: boolean }> {
    const response = await this.client.delete<{ success: boolean }>(
      `/api/tutor-profile/${tutorId}/notes/${noteId}`
    );
    return response.data;
  }

  // Student Feedback endpoints (public - no auth required)
  async validateFeedbackToken(token: string): Promise<FeedbackTokenValidation> {
    try {
      const response = await this.client.post<FeedbackTokenValidation>(
        '/api/feedback/validate-token',
        { token }
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        return {
          valid: false,
          message: 'Token is invalid or expired'
        };
      }
      throw error;
    }
  }

  async submitFeedback(feedbackData: StudentFeedbackSubmission): Promise<FeedbackSubmissionResponse> {
    const response = await this.client.post<FeedbackSubmissionResponse>(
      '/api/feedback/submit',
      feedbackData
    );
    return response.data;
  }

  // Data Retention & Compliance endpoints (admin only)
  async scanRetention(dryRun: boolean = true): Promise<RetentionScanResult> {
    const response = await this.client.post<{ success: boolean; data: RetentionScanResult }>(
      '/api/data-retention/scan',
      { dry_run: dryRun }
    );
    return response.data.data;
  }

  async archiveEntity(request: ArchivalRequest): Promise<ArchivalResult> {
    const response = await this.client.post<{ success: boolean; data: ArchivalResult }>(
      '/api/data-retention/archive',
      request
    );
    return response.data.data;
  }

  async anonymizeEntity(request: AnonymizationRequest): Promise<AnonymizationResult> {
    const response = await this.client.post<{ success: boolean; data: AnonymizationResult }>(
      '/api/data-retention/anonymize',
      request
    );
    return response.data.data;
  }

  async deleteUserData(request: DeletionRequest): Promise<DeletionResult> {
    const response = await this.client.post<{ success: boolean; data: DeletionResult }>(
      '/api/data-retention/delete',
      request
    );
    return response.data.data;
  }

  async getRetentionReport(startDate?: string, endDate?: string): Promise<RetentionReport> {
    const params: Record<string, string> = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;

    const response = await this.client.get<{ success: boolean; data: RetentionReport }>(
      '/api/data-retention/report',
      { params }
    );
    return response.data.data;
  }

  async getRetentionPolicy(): Promise<RetentionPolicy> {
    const response = await this.client.get<{ success: boolean; data: RetentionPolicy }>(
      '/api/data-retention/retention-policy'
    );
    return response.data.data;
  }

  async checkRetentionStatus(entityType: string, entityId: string): Promise<RetentionStatusCheck> {
    const response = await this.client.get<{ success: boolean; data: RetentionStatusCheck }>(
      `/api/data-retention/check/${entityType}/${entityId}`
    );
    return response.data.data;
  }

  async runScheduledArchival(performActions: boolean = false): Promise<any> {
    const response = await this.client.post<{ success: boolean; data: any }>(
      '/api/data-retention/scheduled-archival',
      { perform_actions: performActions }
    );
    return response.data.data;
  }

  // Gamification endpoints
  async getTutorBadges(tutorId: string): Promise<any> {
    const response = await this.client.get(`/api/gamification/${tutorId}/badges`);
    return response.data;
  }

  async getPeerComparison(tutorId: string): Promise<any> {
    const response = await this.client.get(`/api/gamification/${tutorId}/peer-comparison`);
    return response.data;
  }

  // Tutor Goals endpoints
  async getTutorGoals(tutorId: string): Promise<any> {
    const response = await this.client.get(`/api/tutor-goals/${tutorId}`);
    return response.data;
  }

  async createTutorGoal(tutorId: string, goalData: {
    goal_type: string;
    target_value: number;
    target_date: string;
    custom_title?: string;
    custom_description?: string;
  }): Promise<any> {
    const response = await this.client.post(`/api/tutor-goals/${tutorId}`, goalData);
    return response.data;
  }

  async deleteTutorGoal(tutorId: string, goalId: string): Promise<any> {
    const response = await this.client.delete(`/api/tutor-goals/${tutorId}/${goalId}`);
    return response.data;
  }

  // Training Resources endpoints
  async getTrainingResources(params?: {
    tutor_id?: string;
    category?: string;
    resource_type?: string;
    search?: string;
  }): Promise<any> {
    const response = await this.client.get('/api/training-resources/', { params });
    return response.data;
  }

  async updateResourceProgress(tutorId: string, resourceId: string, completed: boolean): Promise<any> {
    const response = await this.client.post(
      `/api/training-resources/${tutorId}/${resourceId}/progress`,
      { completed }
    );
    return response.data;
  }

  // Admin User Management endpoints
  async getAdminUsers(params?: {
    page?: number;
    page_size?: number;
    search?: string;
    role?: string;
    is_active?: boolean;
  }): Promise<any> {
    const response = await this.client.get('/api/admin/users', { params });
    return response.data;
  }

  async createAdminUser(userData: {
    email: string;
    full_name: string;
    roles: string[];
    password?: string;
    is_active?: boolean;
    tutor_id?: string;
    student_id?: string;
  }): Promise<any> {
    const response = await this.client.post('/api/admin/users', userData);
    return response.data;
  }

  async updateAdminUser(userId: number, userData: {
    full_name?: string;
    roles?: string[];
    is_active?: boolean;
  }): Promise<any> {
    const response = await this.client.patch(`/api/admin/users/${userId}`, userData);
    return response.data;
  }

  async deactivateUser(userId: number): Promise<any> {
    const response = await this.client.post(`/api/admin/users/${userId}/deactivate`);
    return response.data;
  }

  async bulkAssignRoles(data: {
    user_ids: number[];
    roles_to_add?: string[];
    roles_to_remove?: string[];
  }): Promise<any> {
    const response = await this.client.post('/api/admin/users/bulk/assign-roles', data);
    return response.data;
  }

  async resetUserPassword(userId: number, newPassword: string): Promise<any> {
    const response = await this.client.post(
      `/api/admin/users/${userId}/reset-password`,
      { new_password: newPassword }
    );
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
