/**
 * Utility functions
 */

import { clsx, type ClassValue } from 'clsx';

// Class name utility
export function cn(...inputs: ClassValue[]) {
    return clsx(inputs);
}

// Format currency (TRY)
export function formatCurrency(value: number | string | null | undefined): string {
    if (value === null || value === undefined) return '-';
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(num)) return '-';

    return new Intl.NumberFormat('tr-TR', {
        style: 'currency',
        currency: 'TRY',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(num);
}

// Format percentage
export function formatPercent(value: number | string | null | undefined): string {
    if (value === null || value === undefined) return '-';
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(num)) return '-';

    return `%${num.toFixed(2)}`;
}

// Format number
export function formatNumber(value: number | string | null | undefined): string {
    if (value === null || value === undefined) return '-';
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(num)) return '-';

    return new Intl.NumberFormat('tr-TR').format(num);
}

// Format date
export function formatDate(date: string | Date | null | undefined): string {
    if (!date) return '-';
    const d = typeof date === 'string' ? new Date(date) : date;

    return new Intl.DateTimeFormat('tr-TR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    }).format(d);
}

// Format datetime
export function formatDateTime(date: string | Date | null | undefined): string {
    if (!date) return '-';
    const d = typeof date === 'string' ? new Date(date) : date;

    return new Intl.DateTimeFormat('tr-TR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    }).format(d);
}

// Get profit color class
export function getProfitColor(value: number | string | null | undefined): string {
    if (value === null || value === undefined) return '';
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(num)) return '';

    return num >= 0 ? 'positive' : 'negative';
}

// Order status badge styles
export function getStatusBadge(status: string): { class: string; label: string } {
    const statusMap: Record<string, { class: string; label: string }> = {
        Created: { class: 'badge-info', label: 'Oluşturuldu' },
        Picking: { class: 'badge-warning', label: 'Hazırlanıyor' },
        Invoiced: { class: 'badge-info', label: 'Faturalandı' },
        Shipped: { class: 'badge-info', label: 'Kargoda' },
        Delivered: { class: 'badge-success', label: 'Teslim Edildi' },
        Cancelled: { class: 'badge-danger', label: 'İptal' },
        Returned: { class: 'badge-danger', label: 'İade' },
        UnDelivered: { class: 'badge-danger', label: 'Teslim Edilemedi' },
    };

    return statusMap[status] || { class: 'badge-info', label: status };
}

// Sync status badge styles
export function getSyncStatusBadge(status: string): { class: string; label: string } {
    const statusMap: Record<string, { class: string; label: string }> = {
        idle: { class: 'badge-info', label: 'Beklemede' },
        syncing: { class: 'badge-warning', label: 'Senkronize Ediliyor' },
        completed: { class: 'badge-success', label: 'Tamamlandı' },
        error: { class: 'badge-danger', label: 'Hata' },
    };

    return statusMap[status] || { class: 'badge-info', label: status };
}
