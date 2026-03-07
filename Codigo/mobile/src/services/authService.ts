import apiClient from '@/api/client';
import { saveToken } from '@/storage/tokenStorage';

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface UserProfile {
  uid: string;
  name: string;
  email: string;
  is_active: boolean;
}

export const authService = {
  async register(payload: RegisterPayload): Promise<UserProfile> {
    const { data } = await apiClient.post<UserProfile>('/auth/register', payload);
    return data;
  },

  async login(payload: LoginPayload): Promise<void> {
    const formData = new URLSearchParams();
    formData.append('username', payload.email);
    formData.append('password', payload.password);

    const { data } = await apiClient.post<{ access_token: string; token_type: string }>(
      '/auth/login',
      formData.toString(),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
    );

    await saveToken(data.access_token);
  },

  async getMe(): Promise<UserProfile> {
    const { data } = await apiClient.get<UserProfile>('/auth/me');
    return data;
  },
};
