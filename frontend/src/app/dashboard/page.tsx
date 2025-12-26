'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsAPI, sellersAPI } from '@/lib/api';
import { formatCurrency, formatPercent, formatNumber, getProfitColor, formatDate } from '@/lib/utils';
import { useAuth } from '@/lib/auth-context';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { DailyProfitChart } from '@/components/charts/DailyProfitChart';
import { CostBreakdownChart } from '@/components/charts/CostBreakdownChart';
import {
    TrendingUp,
    TrendingDown,
    Calendar,
    RefreshCw,
    AlertTriangle,
    Settings,
    Package,
    Tag,
    FileText,
    BarChart3,
    Bell,
    ArrowRight,
    Info,
    Sparkles
} from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
    const { user } = useAuth();
    const [selectedSeller, setSelectedSeller] = useState<number | undefined>();
    const [dateRange, setDateRange] = useState({
        start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
    });

    // Fetch sellers
    const { data: sellers } = useQuery({
        queryKey: ['sellers'],
        queryFn: () => sellersAPI.list(),
    });

    // Fetch dashboard data
    const { data: dashboard, isLoading, refetch } = useQuery({
        queryKey: ['dashboard', selectedSeller, dateRange],
        queryFn: () =>
            analyticsAPI.getDashboard({
                seller_account: selectedSeller,
                ...dateRange,
            }),
    });

    // Fetch daily chart data
    const { data: dailyChart } = useQuery({
        queryKey: ['dailyChart', selectedSeller, dateRange],
        queryFn: () =>
            analyticsAPI.getDailyChart({
                seller_account: selectedSeller,
                ...dateRange,
            }),
    });

    // Fetch cost breakdown
    const { data: costBreakdown } = useQuery({
        queryKey: ['costBreakdown', selectedSeller, dateRange],
        queryFn: () =>
            analyticsAPI.getCostBreakdown({
                seller_account: selectedSeller,
                ...dateRange,
            }),
    });

    const dashboardData = dashboard?.data?.data;
    const chartData = dailyChart?.data?.data || [];
    const costData = costBreakdown?.data?.data || [];

    // Handle sellers data
    const sellerList = Array.isArray(sellers?.data)
        ? sellers.data
        : sellers?.data?.results || sellers?.data?.data || [];

    // Quick action links
    const quickLinks = [
        { label: 'Ürün Ayarları', href: '/products', icon: Package },
        { label: 'Ürün Komisyon Tarifesi', href: '/products', icon: Tag },
        { label: 'Raporlar', href: '/calculations', icon: FileText },
        { label: 'Kâr Marjı Listesi', href: '/calculations', icon: BarChart3 },
        { label: 'Uyarılar', href: '/settings', icon: Bell },
    ];

    // Format date range display
    const formatDateDisplay = (date: string) => {
        const d = new Date(date);
        return d.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' });
    };

    // Get greeting based on time
    const getGreeting = () => {
        const hour = new Date().getHours();
        if (hour < 12) return 'Günaydın';
        if (hour < 18) return 'İyi günler';
        return 'İyi akşamlar';
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header Section */}
                <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
                    {/* Welcome & Store Selection */}
                    <div className="flex-1">
                        <h1 className="text-2xl md:text-3xl font-bold text-slate-800 mb-2">
                            {getGreeting()}, {user?.first_name || 'Kullanıcı'} 👋
                        </h1>

                        <div className="flex items-center gap-3 mb-4">
                            <span className="text-slate-500">Mağaza:</span>
                            <select
                                className="bg-white border border-slate-200 rounded-full px-4 py-1.5 text-sm font-medium text-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500"
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

                        <p className="text-slate-600 mb-2">
                            Seçtiğiniz tarih aralığında, Trendyol mağazanızdaki satışlarınız ortalama{' '}
                            <span className="font-semibold text-primary-600">
                                {formatPercent(dashboardData?.summary?.average_profit_margin || 0)}
                            </span>{' '}
                            kâr marjı ile ilerliyor.
                        </p>

                        <p className="text-slate-500 text-sm">
                            Kârlılığınız hakkında en doğru bilgiyi almak için ürün maliyetlerinizi{' '}
                            <Link href="/products" className="text-primary-600 hover:underline">
                                Ürün Ayarları
                            </Link>{' '}
                            sayfası üzerinden eksiksiz ve güncel tutmalısınız.
                        </p>
                    </div>

                    {/* Date Range Picker */}
                    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
                        <div className="text-sm text-slate-500 mb-2">Tarih Aralığı Seçin:</div>
                        <div className="flex items-center gap-2">
                            <div className="bg-slate-50 rounded-lg px-4 py-2 text-sm font-medium text-slate-700">
                                {formatDateDisplay(dateRange.start_date)} - {formatDateDisplay(dateRange.end_date)}
                            </div>
                            <input
                                type="date"
                                className="opacity-0 absolute w-0 h-0"
                                id="start-date"
                                value={dateRange.start_date}
                                onChange={(e) => setDateRange((prev) => ({ ...prev, start_date: e.target.value }))}
                            />
                            <label htmlFor="start-date" className="p-2 bg-slate-100 rounded-lg hover:bg-slate-200 cursor-pointer transition-colors">
                                <Calendar className="w-5 h-5 text-slate-600" />
                            </label>
                            <button
                                onClick={() => refetch()}
                                className="p-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                            >
                                <RefreshCw className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="flex gap-2 mt-3">
                            <input
                                type="date"
                                className="input text-sm py-1.5"
                                value={dateRange.start_date}
                                onChange={(e) => setDateRange((prev) => ({ ...prev, start_date: e.target.value }))}
                            />
                            <input
                                type="date"
                                className="input text-sm py-1.5"
                                value={dateRange.end_date}
                                onChange={(e) => setDateRange((prev) => ({ ...prev, end_date: e.target.value }))}
                            />
                        </div>
                    </div>
                </div>

                {/* Main Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Kâr Tutarı - Green Card */}
                    <div className="relative overflow-hidden bg-gradient-to-br from-emerald-400 to-emerald-500 rounded-2xl p-5 text-white shadow-lg">
                        <div className="relative z-10">
                            <p className="text-emerald-100 text-sm font-medium mb-1">Kâr Tutarı</p>
                            <p className="text-3xl font-bold mb-2">
                                {isLoading ? (
                                    <span className="inline-block w-28 h-8 bg-white/20 rounded animate-pulse" />
                                ) : (
                                    formatCurrency(dashboardData?.summary?.net_profit || 0)
                                )}
                            </p>
                            <div className="flex items-center gap-1 text-emerald-100 text-sm">
                                <TrendingUp className="w-4 h-4" />
                                <span>Bu dönem</span>
                            </div>
                        </div>
                        <div className="absolute -right-4 -bottom-4 opacity-20">
                            <TrendingUp className="w-32 h-32" />
                        </div>
                        <button className="absolute bottom-3 right-3 bg-white/20 hover:bg-white/30 rounded-full p-1.5 transition-colors">
                            <Info className="w-4 h-4" />
                        </button>
                    </div>

                    {/* Kâr/Ürün Maliyet Oranı - Light Card */}
                    <div className="relative overflow-hidden bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                        <p className="text-slate-500 text-sm font-medium mb-1">Kâr / Ürün Maliyet Oranı</p>
                        <p className="text-3xl font-bold text-slate-800 mb-2">
                            {isLoading ? (
                                <span className="inline-block w-20 h-8 bg-slate-200 rounded animate-pulse" />
                            ) : (
                                formatPercent(dashboardData?.summary?.cost_to_profit_ratio || 84.62)
                            )}
                        </p>
                        <div className="flex items-center gap-1 text-slate-500 text-sm">
                            <BarChart3 className="w-4 h-4" />
                            <span>Maliyet verimliliği</span>
                        </div>
                        <button className="absolute bottom-3 right-3 bg-emerald-100 hover:bg-emerald-200 rounded-full p-1.5 transition-colors text-emerald-600">
                            <Info className="w-4 h-4" />
                        </button>
                    </div>

                    {/* Kâr/Satış Fiyatı Oranı - Yellow Card */}
                    <div className="relative overflow-hidden bg-gradient-to-br from-amber-300 to-amber-400 rounded-2xl p-5 text-amber-900 shadow-lg">
                        <div className="relative z-10">
                            <p className="text-amber-700 text-sm font-medium mb-1">Kâr / Satış Fiyatı Oranı</p>
                            <p className="text-3xl font-bold mb-2">
                                {isLoading ? (
                                    <span className="inline-block w-20 h-8 bg-white/30 rounded animate-pulse" />
                                ) : (
                                    formatPercent(dashboardData?.summary?.average_profit_margin || 0)
                                )}
                            </p>
                            <div className="flex items-center gap-1 text-amber-700 text-sm">
                                <TrendingUp className="w-4 h-4" />
                                <span>Kâr marjı</span>
                            </div>
                        </div>
                        <div className="absolute -right-4 -bottom-4 opacity-20">
                            <Sparkles className="w-32 h-32" />
                        </div>
                        <button className="absolute bottom-3 right-3 bg-white/20 hover:bg-white/30 rounded-full p-1.5 transition-colors">
                            <Info className="w-4 h-4" />
                        </button>
                    </div>

                    {/* Ciro - Light Card */}
                    <div className="relative overflow-hidden bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                        <p className="text-slate-500 text-sm font-medium mb-1">Ciro</p>
                        <p className="text-3xl font-bold text-slate-800 mb-2">
                            {isLoading ? (
                                <span className="inline-block w-28 h-8 bg-slate-200 rounded animate-pulse" />
                            ) : (
                                formatCurrency(dashboardData?.summary?.total_revenue || 0)
                            )}
                        </p>
                        <div className="flex items-center gap-1 text-slate-500 text-sm">
                            <Package className="w-4 h-4" />
                            <span>{formatNumber(dashboardData?.summary?.total_orders || 0)} sipariş</span>
                        </div>
                        <button className="absolute bottom-3 right-3 bg-amber-100 hover:bg-amber-200 rounded-full p-1.5 transition-colors text-amber-600">
                            <Info className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="space-y-3">
                    <h3 className="text-sm font-medium text-slate-500">Son Aktiviteleriniz</h3>
                    <div className="flex flex-wrap gap-2">
                        {quickLinks.map((link) => (
                            <Link
                                key={link.label}
                                href={link.href}
                                className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-full text-sm text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-colors"
                            >
                                <link.icon className="w-4 h-4" />
                                {link.label}
                                <ArrowRight className="w-3 h-3 text-slate-400" />
                            </Link>
                        ))}
                    </div>
                </div>

                {/* Promotional Banner */}
                <div className="bg-gradient-to-r from-primary-50 to-amber-50 border border-primary-100 rounded-2xl p-5 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center">
                            <Sparkles className="w-6 h-6 text-primary-600" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-slate-800">
                                Satışlarını ve kârını artırmak için promosyon karlılık analiziyle kampanyalara katılın sağla!
                            </h3>
                            <p className="text-sm text-slate-500">
                                Kampanya bazlı kârlılık raporlarınızı inceleyin ve en verimli promosyonları belirleyin.
                            </p>
                        </div>
                    </div>
                    <button className="shrink-0 btn-primary whitespace-nowrap">
                        Kârlılık Analizlerini İncele
                    </button>
                </div>

                {/* Warning Banner */}
                {(dashboardData?.data_quality?.items_without_cost > 0 || !dashboardData) && (
                    <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
                        <AlertTriangle className="w-5 h-5 text-red-500 shrink-0" />
                        <p className="text-red-700 text-sm">
                            <span className="font-medium">* Maliyeti girilmemiş ürünleriniz varsa</span> bu ürünlerden gelen siparişler ciroya yansımaz.
                            {dashboardData?.data_quality?.items_without_cost && (
                                <span className="ml-1">
                                    ({dashboardData.data_quality.items_without_cost} ürün maliyetsiz)
                                </span>
                            )}
                        </p>
                        <Link href="/products" className="shrink-0 text-red-600 hover:text-red-700 font-medium text-sm">
                            Maliyetleri Gir →
                        </Link>
                    </div>
                )}

                {/* Charts Section */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Profit Performance Chart */}
                    <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-lg font-semibold text-slate-800">
                                Kâr Performansı ({formatDateDisplay(dateRange.start_date)} ... {formatDateDisplay(dateRange.end_date)})
                            </h2>
                        </div>
                        <DailyProfitChart data={chartData} />
                    </div>

                    {/* Cost Distribution Chart */}
                    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
                        <h2 className="text-lg font-semibold text-slate-800 mb-6">Ciro İçerik Dağılımı (%)</h2>
                        <CostBreakdownChart data={costData} />
                    </div>
                </div>

                {/* Additional Stats Row */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
                        <p className="text-sm text-slate-500 mb-1">Toplam Sipariş</p>
                        <p className="text-2xl font-bold text-slate-800">
                            {formatNumber(dashboardData?.summary?.total_orders || 0)}
                        </p>
                    </div>
                    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
                        <p className="text-sm text-slate-500 mb-1">Toplam Ürün</p>
                        <p className="text-2xl font-bold text-slate-800">
                            {formatNumber(dashboardData?.summary?.total_items || 0)}
                        </p>
                    </div>
                    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
                        <p className="text-sm text-slate-500 mb-1">Toplam Komisyon</p>
                        <p className="text-2xl font-bold text-red-500">
                            {formatCurrency(dashboardData?.summary?.total_commission || 0)}
                        </p>
                    </div>
                    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
                        <p className="text-sm text-slate-500 mb-1">Toplam Kargo</p>
                        <p className="text-2xl font-bold text-slate-800">
                            {formatCurrency(dashboardData?.summary?.total_cargo || 0)}
                        </p>
                    </div>
                </div>

                {/* Top/Loss Products Section */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Top Profitable Products */}
                    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                        <div className="bg-gradient-to-r from-emerald-500 to-emerald-600 px-6 py-4">
                            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                                <TrendingUp className="w-5 h-5" />
                                En Kârlı 5 Ürün
                            </h2>
                        </div>
                        <div className="p-4">
                            {dashboardData?.top_profitable_products?.length > 0 ? (
                                <div className="space-y-3">
                                    {dashboardData.top_profitable_products.slice(0, 5).map((product: any, index: number) => (
                                        <div key={product.barcode} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                                            <span className="w-6 h-6 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center text-sm font-bold">
                                                {index + 1}
                                            </span>
                                            <div className="flex-1 min-w-0">
                                                <p className="font-medium text-slate-800 truncate">{product.product_name}</p>
                                                <p className="text-xs text-slate-500">{product.quantity_sold} adet satıldı</p>
                                            </div>
                                            <div className="text-right">
                                                <p className="font-semibold text-emerald-600">{formatCurrency(product.total_profit)}</p>
                                                <p className="text-xs text-slate-500">{formatPercent(product.avg_margin)} marj</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-center text-slate-400 py-8">Henüz veri yok</p>
                            )}
                        </div>
                    </div>

                    {/* Loss Making Products */}
                    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                        <div className="bg-gradient-to-r from-red-500 to-red-600 px-6 py-4">
                            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                                <TrendingDown className="w-5 h-5" />
                                Zararlı 5 Ürün
                            </h2>
                        </div>
                        <div className="p-4">
                            {dashboardData?.loss_making_products?.length > 0 ? (
                                <div className="space-y-3">
                                    {dashboardData.loss_making_products.slice(0, 5).map((product: any, index: number) => (
                                        <div key={product.barcode} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                                            <span className="w-6 h-6 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-sm font-bold">
                                                {index + 1}
                                            </span>
                                            <div className="flex-1 min-w-0">
                                                <p className="font-medium text-slate-800 truncate">{product.product_name}</p>
                                                <p className="text-xs text-slate-500">{product.quantity_sold} adet satıldı</p>
                                            </div>
                                            <div className="text-right">
                                                <p className="font-semibold text-red-600">{formatCurrency(product.total_loss)}</p>
                                                <p className="text-xs text-slate-500">{formatPercent(product.avg_margin)} marj</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-center text-slate-400 py-8">Zararlı ürün yok 🎉</p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Today's Ordered Products Section */}
                <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                    <div className="bg-gradient-to-r from-orange-400 to-orange-500 px-6 py-4 flex items-center justify-between">
                        <h2 className="text-lg font-semibold text-white">
                            Bugün Sipariş Alan Ürünler
                            <span className="text-orange-100 text-sm font-normal ml-2">
                                (Maliyeti eksik ürünler kârlılık hesaplamasına dahil edilememektedir!)
                            </span>
                        </h2>
                        <div className="flex items-center gap-2">
                            <button className="bg-primary-500 hover:bg-primary-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition-colors">
                                Filtrele ▼
                            </button>
                            <button className="bg-slate-700 hover:bg-slate-800 text-white px-3 py-1.5 rounded-lg text-sm">
                                A+
                            </button>
                            <span className="bg-white text-slate-700 px-3 py-1.5 rounded-lg text-sm font-medium">
                                100%
                            </span>
                            <button className="bg-slate-700 hover:bg-slate-800 text-white px-3 py-1.5 rounded-lg text-sm">
                                A-
                            </button>
                            <button className="bg-slate-700 hover:bg-slate-800 text-white p-1.5 rounded-lg">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                                </svg>
                            </button>
                        </div>
                    </div>
                    <div className="p-6">
                        {dashboardData?.today_orders?.length > 0 ? (
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-slate-200">
                                            <th className="text-left py-3 px-4 font-medium text-slate-600">Ürün</th>
                                            <th className="text-left py-3 px-4 font-medium text-slate-600">Barkod</th>
                                            <th className="text-right py-3 px-4 font-medium text-slate-600">Satış Fiyatı</th>
                                            <th className="text-right py-3 px-4 font-medium text-slate-600">Maliyet</th>
                                            <th className="text-right py-3 px-4 font-medium text-slate-600">Kâr</th>
                                            <th className="text-right py-3 px-4 font-medium text-slate-600">Marj %</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {dashboardData.today_orders.map((order: any) => (
                                            <tr key={order.id} className="border-b border-slate-100 hover:bg-slate-50">
                                                <td className="py-3 px-4">
                                                    <p className="font-medium text-slate-800 truncate max-w-xs">{order.product_name}</p>
                                                </td>
                                                <td className="py-3 px-4 text-slate-600 font-mono text-sm">{order.barcode}</td>
                                                <td className="py-3 px-4 text-right text-slate-800">{formatCurrency(order.sale_price)}</td>
                                                <td className="py-3 px-4 text-right text-slate-600">{formatCurrency(order.cost)}</td>
                                                <td className={`py-3 px-4 text-right font-semibold ${order.profit >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                                                    {formatCurrency(order.profit)}
                                                </td>
                                                <td className={`py-3 px-4 text-right font-medium ${order.margin >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                                                    {formatPercent(order.margin)}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <p className="text-slate-400 text-lg">Veri yok!</p>
                            </div>
                        )}
                        <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-200 text-sm text-slate-500">
                            <div className="flex gap-4">
                                <span>Geçerli sayfa: <strong className="text-slate-700">1</strong></span>
                                <span>Toplam kayıt sayısı: <strong className="text-primary-600">{dashboardData?.today_orders?.length || 0}</strong></span>
                            </div>
                            <span>Sayfa başına gösterilen kayıt sayısı: <strong>50</strong></span>
                        </div>
                    </div>
                </div>

                {/* Order Profitability Analysis Section */}
                <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                    <div className="bg-gradient-to-r from-orange-400 to-orange-500 px-6 py-4 flex items-center justify-between">
                        <h2 className="text-lg font-semibold text-white">
                            Sipariş Kârlılık Analizi
                        </h2>
                        <div className="flex items-center gap-2">
                            <button className="bg-primary-500 hover:bg-primary-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium transition-colors">
                                Filtrele ▼
                            </button>
                            <button className="bg-slate-700 hover:bg-slate-800 text-white px-3 py-1.5 rounded-lg text-sm">
                                A+
                            </button>
                            <span className="bg-white text-slate-700 px-3 py-1.5 rounded-lg text-sm font-medium">
                                85%
                            </span>
                            <button className="bg-slate-700 hover:bg-slate-800 text-white px-3 py-1.5 rounded-lg text-sm">
                                A-
                            </button>
                            <button className="bg-slate-700 hover:bg-slate-800 text-white p-1.5 rounded-lg">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                                </svg>
                            </button>
                        </div>
                    </div>
                    <div className="px-6 pt-2 pb-4 flex justify-end">
                        <button className="bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Raporu İndir
                        </button>
                    </div>
                    <div className="p-6 pt-0">
                        {dashboardData?.order_analysis?.length > 0 ? (
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-slate-200">
                                            <th className="text-left py-3 px-4 font-medium text-slate-600">Sipariş No</th>
                                            <th className="text-left py-3 px-4 font-medium text-slate-600">Tarih</th>
                                            <th className="text-right py-3 px-4 font-medium text-slate-600">Ürün Sayısı</th>
                                            <th className="text-right py-3 px-4 font-medium text-slate-600">Toplam Satış</th>
                                            <th className="text-right py-3 px-4 font-medium text-slate-600">Toplam Maliyet</th>
                                            <th className="text-right py-3 px-4 font-medium text-slate-600">Net Kâr</th>
                                            <th className="text-right py-3 px-4 font-medium text-slate-600">Kâr Marjı</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {dashboardData.order_analysis.map((order: any) => (
                                            <tr key={order.order_number} className="border-b border-slate-100 hover:bg-slate-50">
                                                <td className="py-3 px-4">
                                                    <Link href={`/orders/${order.id}`} className="font-medium text-primary-600 hover:underline">
                                                        {order.order_number}
                                                    </Link>
                                                </td>
                                                <td className="py-3 px-4 text-slate-600">{formatDate(order.order_date)}</td>
                                                <td className="py-3 px-4 text-right text-slate-800">{order.item_count}</td>
                                                <td className="py-3 px-4 text-right text-slate-800">{formatCurrency(order.total_sale)}</td>
                                                <td className="py-3 px-4 text-right text-slate-600">{formatCurrency(order.total_cost)}</td>
                                                <td className={`py-3 px-4 text-right font-semibold ${order.net_profit >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                                                    {formatCurrency(order.net_profit)}
                                                </td>
                                                <td className={`py-3 px-4 text-right font-medium ${order.profit_margin >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                                                    {formatPercent(order.profit_margin)}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <p className="text-slate-400 text-lg">Veri yok!</p>
                            </div>
                        )}
                        <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-200 text-sm text-slate-500">
                            <div className="flex gap-4">
                                <span>Geçerli sayfa: <strong className="text-slate-700">1</strong></span>
                                <span>Toplam kayıt sayısı: <strong className="text-primary-600">{dashboardData?.order_analysis?.length || 0}</strong></span>
                            </div>
                            <span>Sayfa başına gösterilen kayıt sayısı: <strong>50</strong></span>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
