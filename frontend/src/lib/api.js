import axios from 'axios';

const API_BASE = process.env.REACT_APP_BACKEND_URL;

export const api = axios.create({
  baseURL: `${API_BASE}/api`,
});

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('fb_token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !window.location.pathname.startsWith('/login')) {
      localStorage.removeItem('fb_token');
      localStorage.removeItem('fb_user');
    }
    return Promise.reject(err);
  }
);

export const saveAuth = (token, user) => {
  localStorage.setItem('fb_token', token);
  localStorage.setItem('fb_user', JSON.stringify(user));
};

export const getUser = () => {
  try { return JSON.parse(localStorage.getItem('fb_user') || 'null'); } catch { return null; }
};

export const logout = () => {
  localStorage.removeItem('fb_token');
  localStorage.removeItem('fb_user');
  window.location.href = '/login';
};
