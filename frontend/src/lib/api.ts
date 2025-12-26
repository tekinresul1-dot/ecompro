/**
 * API Client for Trendyol Profitability Backend
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const api: AxiosInstance = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && originalRequest) {
            const refreshToken = localStorage.getItem('refresh_token');

            if (refreshToken) {
                try {
                    const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
                        refresh: refreshToken,
                    });

                    const { access } = response.data;
                    localStorage.setItem('access_token', access);

                    originalRequest.headers.Authorization = `Bearer ${access}`;
                    return api(originalRequest);
                } catch {
                    // Refresh failed, logout user
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    window.location.href = '/login';
                }
            }
        }

        return Promise.reject(error);
    }
);

// Auth API
export const authAPI = {
    login: (email: string, password: string) =>
        api.post('/auth/login/', { email, password }),

    register: (data: {
        email: string;
        password: string;
        password_confirm: string;
        first_name: string;
        last_name: string;
        company_name?: string;
    }) => api.post('/auth/register/', data),

    logout: (refresh: string) => api.post('/auth/logout/', { refresh }),

    getProfile: () => api.get('/auth/profile/'),

    updateProfile: (data: object) => api.patch('/auth/profile/', data),

    changePassword: (data: {
        old_password: string;
        new_password: string;
        new_password_confirm: string;
    }) => api.post('/auth/change-password/', data),
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
    }) => api.post('/sellers/', data),

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
