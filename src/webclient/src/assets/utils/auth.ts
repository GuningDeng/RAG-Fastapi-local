import { reactive } from "vue";
import { jwtDecode } from "jwt-decode";

interface AuthState {
  token: string | null;
}

interface DecodedToken {
  sub: string;
  exp: number;
  [key: string]: unknown;
}

// Constants
const TOKEN_KEY = "token_raguser";
const SECONDS_PER_DAY = 60 * 60 * 24;
const TIMESTAMP_MULTIPLIER = 1000;

const state = reactive<AuthState>({
  token: null,
});

/**
 * Stores the authentication token in both state and localStorage
 */
const setToken = (token: string): void => {
  state.token = token;
  localStorage.setItem(TOKEN_KEY, token);
};

/**
 * Retrieves the authentication token from state or localStorage
 */
const getToken = (): string | null => {
  if (!state.token) {
    const storedToken = localStorage.getItem(TOKEN_KEY);
    if (storedToken) {
      state.token = storedToken;
    }
  }
  return state.token;
};

/**
 * Checks if token is expired
 */
const isTokenExpired = (exp: number): boolean => {
  const now = Math.floor(Date.now() / TIMESTAMP_MULTIPLIER);
  return exp <= now;
};

/**
 * Extracts user ID from the JWT token if valid and not expired
 */
const getUserId = (): string | null => {
  const token = getToken();
  if (!token) {
    return null;
  }

  try {
    const decodedToken = jwtDecode<DecodedToken>(token);
    
    if (isTokenExpired(decodedToken.exp)) {
      return null;
    }

    const daysRemaining = Math.floor((decodedToken.exp - Math.floor(Date.now() / TIMESTAMP_MULTIPLIER)) / SECONDS_PER_DAY);
    console.log(`Token expires in ${daysRemaining} days.`);

    return decodedToken.sub;
  } catch (error) {
    console.error("Failed to decode token:", error);
    return null;
  }
};

/**
 * Clears the authentication token from state and localStorage
 */
const logout = (): void => {
  state.token = null;
  localStorage.removeItem(TOKEN_KEY);
};

/**
 * Checks if user is currently logged in
 */
const checkLoggedIn = (): boolean => {
  return !!getUserId();
};

export default { setToken, getToken, logout, checkLoggedIn, getUserId };
