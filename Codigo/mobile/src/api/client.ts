import axios from 'axios';
import { Platform } from 'react-native';
import { getToken, deleteToken } from '@/storage/tokenStorage';

export const API_BASE_URL =
  Platform.OS === 'android'
    ? 'http://10.0.2.2:8000/api'
    : 'http://localhost:8000/api';

const BASE_URL = API_BASE_URL;

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
});

apiClient.interceptors.request.use(async (config) => {
  const token = await getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await deleteToken();
    }
    return Promise.reject(error);
  },
);

export default apiClient;
