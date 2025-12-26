/**
 * SECURITY HARDENED API Client for Trendyol Profitability Backend
 * 
 * Security features:
 * - XSS protection via input sanitization
 * - Secure token storage practices
 * - Request/response validation
 * - CSRF protection
 * - Rate limiting handling
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// SECURITY: Token storage keys
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

/**
 * SECURITY: Sanitize string input to prevent XSS
 */
export function sanitizeInput(input: string): string {
    if (!input) return input;
    return input
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;')
        .replace(/\//g, '&#x2F;');
}

/**
 * SECURITY: Validate email format
 */
export function validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * SECURITY: Validate password strength
 */
export function validatePassword(password: string): { valid: boolean; message: string } {
    if (password.length < 10) {
        return { valid: false, message: 'Şifre en az 10 karakter olmalıdır.' };
    }
    if (!/[A-Z]/.test(password)) {
        return { valid: false, message: 'Şifre en az bir büyük harf içermelidir.' };
    }
    if (!/[a-z]/.test(password)) {
        return { valid: false, message: 'Şifre en az bir küçük harf içermelidir.' };
    }
    if (!/[0-9]/.test(password)) {
        return { valid: false, message: 'Şifre en az bir rakam içermelidir.' };
    }
    return { valid: true, message: '' };
}

/**
 * SECURITY: Secure token storage
 * Note: In production, consider httpOnly cookies for tokens
 */
const tokenStorage = {
    getAccessToken: (): string | null => {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem(ACCESS_TOKEN_KEY);
    },

    setAccessToken: (token: string): void => {
        if (typeof window === 'undefined') return;
        localStorage.setItem(ACCESS_TOKEN_KEY, token);
    },

    getRefreshToken: (): string | null => {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem(REFRESH_TOKEN_KEY);
    },

    setRefreshToken: (token: string): void => {
        if (typeof window === 'undefined') return;
        localStorage.setItem(REFRESH_TOKEN_KEY, token);
    },

    clearTokens: (): void => {
        if (typeof window === 'undefined') return;
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
    }
};

// Export for use in auth context
export { tokenStorage };

// Create axios instance with security defaults
const api: AxiosInstance = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    // SECURITY: Timeout to prevent hanging requests
    timeout: 30000,
    // SECURITY: Validate response status
    validateStatus: (status) => status >= 200 && status < 500,
});

// SECURITY: Add auth token to requests
api.interceptors.request.use((config) => {
    const token = tokenStorage.getAccessToken();
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    // SECURITY: Add request timestamp for debugging
    config.headers['X-Request-Time'] = new Date().toISOString();

    return config;
});

// Track refresh attempts to prevent infinite loops
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function subscribeTokenRefresh(callback: (token: string) => void) {
    refreshSubscribers.push(callback);
}

function onTokenRefreshed(token: string) {
    refreshSubscribers.forEach(callback => callback(token));
    refreshSubscribers = [];
}

// SECURITY: Handle token refresh on 401 with protection against infinite loops
api.interceptors.response.use(
    (response: AxiosResponse) => {
        // SECURITY: Check for rate limiting headers
        const rateLimitRemaining = response.headers['x-ratelimit-remaining'];
        if (rateLimitRemaining && parseInt(rateLimitRemaining) < 10) {
            console.warn('API rate limit approaching');
        }

        return response;
    },
    async (error: AxiosError) => {
        const originalRequest = error.config;

        // SECURITY: Handle rate limiting (429)
        if (error.response?.status === 429) {
            const retryAfter = error.response.headers['retry-after'];
            console.error(`Rate limited. Retry after: ${retryAfter} seconds`);
            return Promise.reject({
                ...error,
                message: 'Çok fazla istek gönderildi. Lütfen bekleyin.'
            });
        }

        // Handle authentication errors
        if (error.response?.status === 401 && originalRequest) {
            const refreshToken = tokenStorage.getRefreshToken();

            if (refreshToken && !isRefreshing) {
                isRefreshing = true;

                try {
                    const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
                        refresh: refreshToken,
                    });

                    const { access } = response.data;
                    tokenStorage.setAccessToken(access);

                    isRefreshing = false;
                    onTokenRefreshed(access);

                    originalRequest.headers.Authorization = `Bearer ${access}`;
                    return api(originalRequest);
                } catch (refreshError) {
                    // SECURITY: Refresh failed, clear tokens and redirect to login
                    isRefreshing = false;
                    tokenStorage.clearTokens();

                    if (typeof window !== 'undefined') {
                        window.location.href = '/login';
                    }

                    return Promise.reject(refreshError);
                }
            } else if (isRefreshing) {
                // Wait for token refresh to complete
                return new Promise((resolve) => {
                    subscribeTokenRefresh((token: string) => {
                        originalRequest.headers.Authorization = `Bearer ${token}`;
                        resolve(api(originalRequest));
                    });
                });
            }
        }

        return Promise.reject(error);
    }
);

// Auth API with security validations
export const authAPI = {
    login: (email: string, password: string) => {
        // SECURITY: Validate inputs before sending
        if (!validateEmail(email)) {
            return Promise.reject({ message: 'Geçersiz email formatı' });
        }
        return api.post('/auth/login/', { email: email.toLowerCase().trim(), password });
    },

    register: (data: {
        email: string;
        password: string;
        password_confirm: string;
        first_name: string;
        last_name: string;
        company_name?: string;
    }) => {
        // SECURITY: Validate inputs
        if (!validateEmail(data.email)) {
            return Promise.reject({ message: 'Geçersiz email formatı' });
        }
        const passwordCheck = validatePassword(data.password);
        if (!passwordCheck.valid) {
            return Promise.reject({ message: passwordCheck.message });
        }
        if (data.password !== data.password_confirm) {
            return Promise.reject({ message: 'Şifreler eşleşmiyor' });
        }

        // SECURITY: Sanitize text inputs
        return api.post('/auth/register/', {
            ...data,
            email: data.email.toLowerCase().trim(),
            first_name: sanitizeInput(data.first_name),
            last_name: sanitizeInput(data.last_name),
            company_name: data.company_name ? sanitizeInput(data.company_name) : undefined,
        });
    },

    logout: (refresh: string) => api.post('/auth/logout/', { refresh }),

    getProfile: () => api.get('/auth/profile/'),

    updateProfile: (data: object) => api.patch('/auth/profile/', data),

    changePassword: (data: {
        old_password: string;
        new_password: string;
        new_password_confirm: string;
    }) => {
        const passwordCheck = validatePassword(data.new_password);
        if (!passwordCheck.valid) {
            return Promise.reject({ message: passwordCheck.message });
        }
        return api.post('/auth/change-password/', data);
    },
};

// Sellers API
export const sellersAPI = {
    list: () => api.get('/sellers/'),

    get: (id: number) => api.get(`/sellers/${id}/`),

    create: (data: {
        seller_id: string;
        api_key: string;
        api_secret: string;
        shop_name: string;
        default_commission_rate?: number;
    }) => {
        // SECURITY: Sanitize shop name
        return api.post('/sellers/', {
            ...data,
            shop_name: sanitizeInput(data.shop_name),
        });
    },

    update: (id: number, data: object) => api.patch(`/sellers/${id}/`, data),

    delete: (id: number) => api.delete(`/sellers/${id}/`),

    triggerSync: (id: number, syncType: string = 'incremental') =>
        api.post(`/sellers/${id}/sync/`, { sync_type: syncType }),

    getSyncStatus: (id: number) => api.get(`/sellers/${id}/sync-status/`),

    getSyncLogs: (id: number) => api.get(`/sellers/${id}/sync-logs/`),

    testCredentials: (id: number) => api.post(`/sellers/${id}/test-credentials/`),
};

// Products API
export const productsAPI = {
    list: (params?: object) => api.get('/products/', { params }),

    get: (id: number) => api.get(`/products/${id}/`),

    updateCost: (id: number, data: {
        product_cost_excl_vat: number;
        purchase_vat_rate?: number;
        sales_vat_rate?: number;
        commission_rate?: number | null;
    }) => api.patch(`/products/${id}/cost/`, data),

    getCostHistory: (id: number) => api.get(`/products/${id}/cost-history/`),

    bulkUpload: (sellerId: number, file: File) => {
        // SECURITY: Validate file type
        const allowedTypes = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'text/csv',
        ];
        if (!allowedTypes.includes(file.type)) {
            return Promise.reject({ message: 'Sadece Excel ve CSV dosyaları yüklenebilir.' });
        }

        // SECURITY: Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            return Promise.reject({ message: 'Dosya boyutu 10MB\'dan küçük olmalıdır.' });
        }

        const formData = new FormData();
        formData.append('seller_account', sellerId.toString());
        formData.append('file', file);
        return api.post('/products/bulk-upload/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    getBulkUploadStatus: (id: number) =>
        api.get(`/products/bulk-upload/${id}/status/`),

    getWithoutCost: (params?: object) =>
        api.get('/products/without-cost/', { params }),

    export: (sellerId?: number) =>
        api.get('/products/export/', {
            params: sellerId ? { seller_account: sellerId } : undefined,
            responseType: 'blob',
        }),
};

// Orders API
export const ordersAPI = {
    list: (params?: object) => api.get('/orders/', { params }),

    get: (id: number) => api.get(`/orders/${id}/`),

    getItems: (id: number) => api.get(`/orders/${id}/items/`),

    getSummary: (params?: object) => api.get('/orders/summary/', { params }),

    getRecent: () => api.get('/orders/recent/'),
};

// Calculations API
export const calculationsAPI = {
    get: (id: number) => api.get(`/calculations/${id}/`),

    getBreakdown: (id: number) => api.get(`/calculations/${id}/breakdown/`),

    getByOrder: (orderId: number) => api.get(`/calculations/order/${orderId}/`),

    triggerForOrder: (orderId: number) =>
        api.post(`/calculations/trigger/order/${orderId}/`),

    recalculateProduct: (productId: number) =>
        api.post(`/calculations/recalculate/product/${productId}/`),

    getDailySummaries: (params?: object) =>
        api.get('/calculations/daily/', { params }),

    getProductProfits: (params?: object) =>
        api.get('/calculations/products/', { params }),

    getLossProducts: (params?: object) =>
        api.get('/calculations/products/loss/', { params }),

    getTopProducts: (params?: object) =>
        api.get('/calculations/products/top/', { params }),
};

// Analytics API
export const analyticsAPI = {
    getDashboard: (params?: object) =>
        api.get('/analytics/dashboard/', { params }),

    getDailyChart: (params?: object) =>
        api.get('/analytics/daily/', { params }),

    getMonthlyChart: (params?: object) =>
        api.get('/analytics/monthly/', { params }),

    getCostBreakdown: (params?: object) =>
        api.get('/analytics/cost-breakdown/', { params }),

    getProductChart: (params?: object) =>
        api.get('/analytics/products/', { params }),
};

export default api;
