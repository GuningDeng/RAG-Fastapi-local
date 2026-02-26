import axios, { AxiosError } from "axios";
import type { AxiosInstance, InternalAxiosRequestConfig } from "axios";
import authModule from "@/assets/utils/auth";

// Constants
const BASE_URL = "http://localhost:8000";
const REQUEST_TIMEOUT = 90000; // ms

const { getToken, logout } = authModule;

const axiosInstance: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: REQUEST_TIMEOUT,
});

/**
 * Request interceptor to add authentication token to headers
 */
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor to handle authentication errors
 */
axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      console.warn("Unauthorized - logging out user");
      logout();
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;

