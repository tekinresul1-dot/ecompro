'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ordersAPI, sellersAPI } from '@/lib/api';
import { formatCurrency, formatDateTime, getStatusBadge } from '@/lib/utils';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Search, ChevronRight } from 'lucide-react';
import Link from 'next/link';

export default function OrdersPage() {
    const [search, setSearch] = useState('');
    const [selectedSeller, setSelectedSeller] = useState<number | undefined>();
    const [selectedStatus, setSelectedStatus] = useState('');
    const [dateRange, setDateRange] = useState({
        start_date: '',
        end_date: '',
    });

    // Fetch sellers
    const { data: sellers } = useQuery({
        queryKey: ['sellers'],
        queryFn: () => sellersAPI.list(),
    });

    // Fetch orders
    const { data: orders, isLoading } = useQuery({
        queryKey: ['orders', selectedSeller, selectedStatus, dateRange, search],
        queryFn: () =>
            ordersAPI.list({
                seller_account: selectedSeller,
                status: selectedStatus || undefined,
                start_date: dateRange.start_date || undefined,
                end_date: dateRange.end_date || undefined,
                search: search || undefined,
            }),
    });

    // Fetch summary
    const { data: summary } = useQuery({
        queryKey: ['orderSummary', selectedSeller, dateRange],
        queryFn: () =>
            ordersAPI.getSummary({
                seller_account: selectedSeller,
                start_date: dateRange.start_date || undefined,
                end_date: dateRange.end_date || undefined,
            }),
    });

    const orderList = orders?.data?.results || orders?.data || [];
    const summaryData = summary?.data?.data;

    // Handle sellers data - could be array directly or nested
    const sellerList = Array.isArray(sellers?.data)
        ? sellers.data
        : sellers?.data?.results || sellers?.data?.data || [];

    const statusOptions = [
        { value: '', label: 'Tüm Durumlar' },
        { value: 'Created', label: 'Oluşturuldu' },
        { value: 'Picking', label: 'Hazırlanıyor' },
        { value: 'Shipped', label: 'Kargoda' },
        { value: 'Delivered', label: 'Teslim Edildi' },
        { value: 'Cancelled', label: 'İptal' },
        { value: 'Returned', label: 'İade' },
    ];

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <h1 className="text-2xl font-bold text-slate-800">Siparişler</h1>

                {/* Summary Cards */}
                {summaryData && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="stat-card">
                            <p className="text-sm text-slate-500">Toplam Sipariş</p>
                            <p className="stat-value">{summaryData.total_orders}</p>
                        </div>
                        <div className="stat-card">
                            <p className="text-sm text-slate-500">Toplam Ürün</p>
                            <p className="stat-value">{summaryData.total_items}</p>
                        </div>
                        <div className="stat-card">
                            <p className="text-sm text-slate-500">Toplam Gelir</p>
                            <p className="stat-value">{formatCurrency(summaryData.total_revenue)}</p>
                        </div>
                        <div className="stat-card">
                            <p className="text-sm text-slate-500">Toplam İndirim</p>
                            <p className="stat-value">{formatCurrency(summaryData.total_discount)}</p>
                        </div>
                    </div>
                )}

                {/* Filters */}
                <div className="card">
                    <div className="flex flex-wrap gap-4">
                        <div className="flex-1 min-w-[200px]">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                <input
                                    type="text"
                                    className="input pl-10"
                                    placeholder="Sipariş numarası ara..."
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                />
                            </div>
                        </div>

                        <select
                            className="input w-44"
                            value={selectedSeller || ''}
                            onChange={(e) => setSelectedSeller(e.target.value ? Number(e.target.value) : undefined)}
                        >
                            <option value="">Tüm Mağazalar</option>
                            {sellerList.map((seller: any) => (
                                <option key={seller.id} value={seller.id}>
                                    {seller.shop_name}
                                </option>
                            ))}
                        </select>

                        <select
                            className="input w-40"
                            value={selectedStatus}
                            onChange={(e) => setSelectedStatus(e.target.value)}
                        >
                            {statusOptions.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                    {opt.label}
                                </option>
                            ))}
                        </select>

                        <input
                            type="date"
                            className="input w-40"
                            value={dateRange.start_date}
                            onChange={(e) => setDateRange((p) => ({ ...p, start_date: e.target.value }))}
                        />
                        <input
                            type="date"
                            className="input w-40"
                            value={dateRange.end_date}
                            onChange={(e) => setDateRange((p) => ({ ...p, end_date: e.target.value }))}
                        />
                    </div>
                </div>

                {/* Orders Table */}
                <div className="card p-0">
                    <div className="table-container">
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Sipariş No</th>
                                    <th>Tarih</th>
                                    <th>Durum</th>
                                    <th>Mağaza</th>
                                    <th className="text-right">Tutar</th>
                                    <th className="text-right">Ürün Sayısı</th>
                                    <th className="w-10"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {isLoading ? (
                                    <tr>
                                        <td colSpan={7} className="text-center py-8">
                                            <div className="spinner mx-auto" />
                                        </td>
                                    </tr>
                                ) : orderList.length === 0 ? (
                                    <tr>
                                        <td colSpan={7} className="text-center py-8 text-slate-400">
                                            Sipariş bulunamadı
                                        </td>
                                    </tr>
                                ) : (
                                    orderList.map((order: any) => {
                                        const status = getStatusBadge(order.status);
                                        return (
                                            <tr key={order.id}>
                                                <td className="font-medium">{order.trendyol_order_number}</td>
                                                <td className="text-slate-500">{formatDateTime(order.order_date)}</td>
                                                <td>
                                                    <span className={status.class}>{status.label}</span>
                                                </td>
                                                <td>{order.seller_name}</td>
                                                <td className="text-right font-medium">
                                                    {formatCurrency(order.total_price)}
                                                </td>
                                                <td className="text-right">{order.item_count}</td>
                                                <td>
                                                    <Link
                                                        href={`/orders/${order.id}`}
                                                        className="p-2 text-slate-400 hover:text-primary-500 hover:bg-primary-50 rounded inline-flex"
                                                    >
                                                        <ChevronRight className="w-4 h-4" />
                                                    </Link>
                                                </td>
                                            </tr>
                                        );
                                    })
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
