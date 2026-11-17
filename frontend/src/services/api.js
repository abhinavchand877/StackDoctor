import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('stackdoctor_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token on 401 Unauthorized
      const currentPath = window.location.pathname;
      if (currentPath !== '/login' && currentPath !== '/register' && currentPath !== '/') {
        localStorage.removeItem('stackdoctor_token');
        localStorage.removeItem('stackdoctor_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
};

export const scansAPI = {
  create: (formData) =>
    api.post('/scans', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  list: () => api.get('/scans'),
  get: (id) => api.get(`/scans/${id}`),
  delete: (id) => api.delete(`/scans/${id}`),
  getFindings: (id, params) => api.get(`/scans/${id}/findings`, { params }),
  getScore: (id) => api.get(`/scans/${id}/score`),
  getReadiness: (id) => api.get(`/scans/${id}/readiness`),
  getPdfUrl: (id) => {
    const token = typeof window !== 'undefined' && window.localStorage ? window.localStorage.getItem('stackdoctor_token') : '';
    return `/api/scans/${id}/report/pdf?token=${encodeURIComponent(token || '')}`;
  },
  downloadJson: async (id, projectName) => {
    const res = await api.get(`/scans/${id}/report/json`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `StackDoctor_Report_${projectName || 'project'}_${id}.json`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
  downloadSarif: async (id, projectName) => {
    const res = await api.get(`/scans/${id}/report/sarif`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `StackDoctor_Report_${projectName || 'project'}_${id}.sarif`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },
};

export const systemAPI = {
  health: () => api.get('/health'),
};

export default api;
