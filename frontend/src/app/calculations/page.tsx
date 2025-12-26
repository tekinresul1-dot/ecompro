'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { calculationsAPI, sellersAPI } from '@/lib/api';
import { formatCurrency, formatPercent, formatDate, getProfitColor } from '@/lib/utils';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';

export default function CalculationsPage() {
    const [selectedSeller, setSelectedSeller] = useState<number | undefined>();
    const [dateRange, setDateRange] = useState({
        start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
    });
    const [activeTab, setActiveTab] = useState<'daily' | 'top' | 'loss'>('daily');

    // Fetch sellers
    const { data: sellers } = useQuery({
        queryKey: ['sellers'],
        queryFn: () => sellersAPI.list(),
    });

    // Fetch daily summaries
    const { data: dailySummaries } = useQuery({
        queryKey: ['dailySummaries', selectedSeller, dateRange],
        queryFn: () =>
            calculationsAPI.getDailySummaries({
                seller_account: selectedSeller,
                ...dateRange,
            }),
        enabled: activeTab === 'daily',
    });

    // Fetch top products
    const { data: topProducts } = useQuery({
        queryKey: ['topProducts', selectedSeller],
        queryFn: () =>
            calculationsAPI.getTopProducts({ seller_account: selectedSeller }),
        enabled: activeTab === 'top',
    });

    // Fetch loss products
    const { data: lossProducts } = useQuery({
        queryKey: ['lossProducts', selectedSeller],
        queryFn: () =>
            calculationsAPI.getLossProducts({ seller_account: selectedSeller }),
        enabled: activeTab === 'loss',
    });

    const dailyList = dailySummaries?.data || [];
    const topList = topProducts?.data || [];
    const lossList = lossProducts?.data || [];

    // Handle sellers data - could be array directly or nested
    const sellerList = Array.isArray(sellers?.data)
        ? sellers.data
        : sellers?.data?.results || sellers?.data?.data || [];

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <h1 className="text-2xl font-bold text-slate-800">Kâr Hesaplamaları</h1>

                    <div className="flex gap-4">
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
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 border-b border-slate-200">
                    <button
                        onClick={() => setActiveTab('daily')}
                        className={`px-4 py-2 -mb-px text-sm font-medium transition-colors ${activeTab === 'daily'
                            ? 'text-primary-600 border-b-2 border-primary-500'
                            : 'text-slate-500 hover:text-slate-700'
                            }`}
                    >
                        Günlük Özetler
                    </button>
                    <button
                        onClick={() => setActiveTab('top')}
                        className={`px-4 py-2 -mb-px text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'top'
                            ? 'text-primary-600 border-b-2 border-primary-500'
                            : 'text-slate-500 hover:text-slate-700'
                            }`}
                    >
                        <TrendingUp className="w-4 h-4" />
                        En Kârlı Ürünler
                    </button>
                    <button
                        onClick={() => setActiveTab('loss')}
                        className={`px-4 py-2 -mb-px text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'loss'
                            ? 'text-primary-600 border-b-2 border-primary-500'
                            : 'text-slate-500 hover:text-slate-700'
                            }`}
                    >
                        <TrendingDown className="w-4 h-4" />
                        Zararlı Ürünler
                    </button>
                </div>

                {/* Tab Content */}
                {activeTab === 'daily' && (
                    <div className="space-y-4">
                        {/* Date Range */}
                        <div className="flex gap-4">
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

                        {/* Daily Summary Table */}
                        <div className="card p-0">
                            <div className="table-container">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th>Tarih</th>
                                            <th className="text-right">Sipariş</th>
                                            <th className="text-right">Ürün</th>
                                            <th className="text-right">Gelir</th>
                                            <th className="text-right">Maliyet</th>
                                            <th className="text-right">Kâr</th>
                                            <th className="text-right">Marj</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {dailyList.length === 0 ? (
                                            <tr>
                                                <td colSpan={7} className="text-center py-8 text-slate-400">
                                                    Veri bulunamadı
                                                </td>
                                            </tr>
                                        ) : (
                                            dailyList.map((day: any) => (
                                                <tr key={day.id}>
                                                    <td className="font-medium">{formatDate(day.date)}</td>
                                                    <td className="text-right">{day.total_orders}</td>
                                                    <td className="text-right">{day.total_items}</td>
                                                    <td className="text-right">{formatCurrency(day.total_revenue)}</td>
                                                    <td className="text-right">{formatCurrency(day.total_cost)}</td>
                                                    <td className={`text-right font-medium ${getProfitColor(day.total_profit)}`}>
                                                        {formatCurrency(day.total_profit)}
                                                    </td>
                                                    <td className={`text-right ${getProfitColor(day.average_margin)}`}>
                                                        {formatPercent(day.average_margin)}
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'top' && (
                    <div className="card p-0">
                        <div className="table-container">
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>Barkod</th>
                                        <th>Ürün</th>
                                        <th className="text-right">Satış Adedi</th>
                                        <th className="text-right">Toplam Gelir</th>
                                        <th className="text-right">Toplam Kâr</th>
                                        <th className="text-right">Ortalama Marj</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {topList.length === 0 ? (
                                        <tr>
                                            <td colSpan={6} className="text-center py-8 text-slate-400">
                                                Kârlı ürün bulunamadı
                                            </td>
                                        </tr>
                                    ) : (
                                        topList.map((product: any) => (
                                            <tr key={product.id}>
                                                <td className="font-mono text-sm">{product.barcode}</td>
                                                <td>
                                                    <div className="max-w-xs truncate">{product.product_name}</div>
                                                </td>
                                                <td className="text-right">{product.total_quantity_sold}</td>
                                                <td className="text-right">{formatCurrency(product.total_revenue)}</td>
                                                <td className="text-right font-medium positive">
                                                    {formatCurrency(product.total_profit)}
                                                </td>
                                                <td className="text-right positive">
                                                    {formatPercent(product.average_margin)}
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {activeTab === 'loss' && (
                    <>
                        {lossList.length > 0 && (
                            <div className="bg-danger-50 border border-danger-200 rounded-lg p-4 flex items-start gap-3">
                                <AlertTriangle className="w-5 h-5 text-danger-500 mt-0.5" />
                                <div>
                                    <h3 className="font-medium text-danger-800">Dikkat!</h3>
                                    <p className="text-sm text-danger-700">
                                        {lossList.length} ürün zarar ettiriyor. Bu ürünlerin fiyatlarını veya
                                        maliyetlerini gözden geçirmenizi öneririz.
                                    </p>
                                </div>
                            </div>
                        )}

                        <div className="card p-0">
                            <div className="table-container">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th>Barkod</th>
                                            <th>Ürün</th>
                                            <th className="text-right">Maliyet</th>
                                            <th className="text-right">Satış Adedi</th>
                                            <th className="text-right">Toplam Zarar</th>
                                            <th className="text-right">Ortalama Marj</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {lossList.length === 0 ? (
                                            <tr>
                                                <td colSpan={6} className="text-center py-8 text-slate-400">
                                                    Zararlı ürün bulunamadı 🎉
                                                </td>
                                            </tr>
                                        ) : (
                                            lossList.map((product: any) => (
                                                <tr key={product.id}>
                                                    <td className="font-mono text-sm">{product.barcode}</td>
                                                    <td>
                                                        <div className="max-w-xs truncate">{product.product_name}</div>
                                                    </td>
                                                    <td className="text-right">{formatCurrency(product.product_cost)}</td>
                                                    <td className="text-right">{product.total_quantity_sold}</td>
                                                    <td className="text-right font-medium negative">
                                                        {formatCurrency(product.total_profit)}
                                                    </td>
                                                    <td className="text-right negative">
                                                        {formatPercent(product.average_margin)}
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </DashboardLayout>
    );
}
