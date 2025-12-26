'use client';

import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ordersAPI, calculationsAPI } from '@/lib/api';
import { formatCurrency, formatDateTime, formatPercent, getStatusBadge, getProfitColor } from '@/lib/utils';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { ArrowLeft, RefreshCw } from 'lucide-react';

export default function OrderDetailPage() {
    const params = useParams();
    const orderId = Number(params.id);

    // Fetch order details
    const { data: order, isLoading: orderLoading } = useQuery({
        queryKey: ['order', orderId],
        queryFn: () => ordersAPI.get(orderId),
        enabled: !!orderId,
    });

    // Fetch calculations for this order
    const { data: calculations } = useQuery({
        queryKey: ['orderCalculations', orderId],
        queryFn: () => calculationsAPI.getByOrder(orderId),
        enabled: !!orderId,
    });

    const orderData = order?.data;
    const calcList = calculations?.data || [];

    if (orderLoading) {
        return (
            <DashboardLayout>
                <div className="flex items-center justify-center h-64">
                    <div className="spinner" />
                </div>
            </DashboardLayout>
        );
    }

    if (!orderData) {
        return (
            <DashboardLayout>
                <div className="text-center py-12">
                    <p className="text-slate-500">Sipariş bulunamadı.</p>
                    <Link href="/orders" className="text-primary-500 hover:underline mt-2 inline-block">
                        Siparişlere Dön
                    </Link>
                </div>
            </DashboardLayout>
        );
    }

    const status = getStatusBadge(orderData.status);

    // Calculate totals from calculations
    const totalProfit = calcList.reduce(
        (sum: number, c: any) => sum + parseFloat(c.net_profit || 0),
        0
    );

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center gap-4">
                    <Link
                        href="/orders"
                        className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5 text-slate-500" />
                    </Link>
                    <div className="flex-1">
                        <h1 className="text-2xl font-bold text-slate-800">
                            Sipariş #{orderData.trendyol_order_number}
                        </h1>
                        <p className="text-sm text-slate-500">
                            {formatDateTime(orderData.order_date)}
                        </p>
                    </div>
                    <span className={status.class}>{status.label}</span>
                </div>

                {/* Order Info */}
                <div className="grid md:grid-cols-3 gap-4">
                    <div className="stat-card">
                        <p className="text-sm text-slate-500">Toplam Tutar</p>
                        <p className="stat-value">{formatCurrency(orderData.total_price)}</p>
                    </div>
                    <div className="stat-card">
                        <p className="text-sm text-slate-500">İndirim</p>
                        <p className="stat-value">{formatCurrency(orderData.total_discount)}</p>
                    </div>
                    <div className="stat-card">
                        <p className="text-sm text-slate-500">Net Kâr</p>
                        <p className={`stat-value ${getProfitColor(totalProfit)}`}>
                            {formatCurrency(totalProfit)}
                        </p>
                    </div>
                </div>

                {/* Shipping Info */}
                <div className="card">
                    <h2 className="card-header">Kargo Bilgileri</h2>
                    <div className="grid md:grid-cols-3 gap-4 text-sm">
                        <div>
                            <span className="text-slate-500">Kargo Şirketi</span>
                            <p className="font-medium">{orderData.cargo_company || '-'}</p>
                        </div>
                        <div>
                            <span className="text-slate-500">Takip No</span>
                            <p className="font-medium">{orderData.cargo_tracking_number || '-'}</p>
                        </div>
                        <div>
                            <span className="text-slate-500">Kargoya Verilme</span>
                            <p className="font-medium">{formatDateTime(orderData.shipped_at) || '-'}</p>
                        </div>
                    </div>
                </div>

                {/* Order Items with Calculations */}
                <div className="card p-0">
                    <div className="p-6 border-b border-slate-200">
                        <h2 className="text-lg font-semibold text-slate-800">
                            Sipariş Kalemleri ({orderData.items?.length || 0})
                        </h2>
                    </div>

                    <div className="divide-y divide-slate-100">
                        {orderData.items?.map((item: any) => {
                            const calc = calcList.find((c: any) => c.order_item === item.id);

                            return (
                                <div key={item.id} className="p-6">
                                    {/* Item Header */}
                                    <div className="flex items-start justify-between mb-4">
                                        <div>
                                            <h3 className="font-medium text-slate-800">{item.product_name}</h3>
                                            <p className="text-sm text-slate-500">
                                                Barkod: {item.barcode} | Adet: {item.quantity}
                                            </p>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-medium">{formatCurrency(item.unit_price)}</p>
                                            {item.discount_amount > 0 && (
                                                <p className="text-sm text-danger-500">
                                                    -{formatCurrency(item.discount_amount)}
                                                </p>
                                            )}
                                        </div>
                                    </div>

                                    {/* Calculation Breakdown */}
                                    {calc ? (
                                        <div className="bg-slate-50 rounded-lg p-4">
                                            <h4 className="text-sm font-medium text-slate-700 mb-3">
                                                Kâr Hesaplaması
                                            </h4>
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                                <div>
                                                    <span className="text-slate-500">Net Satış</span>
                                                    <p className="font-medium">
                                                        {formatCurrency(calc.net_sale_price_excl_vat)}
                                                    </p>
                                                </div>
                                                <div>
                                                    <span className="text-slate-500">Ürün Maliyeti</span>
                                                    <p className="font-medium">
                                                        {calc.has_cost_data
                                                            ? formatCurrency(calc.product_cost_excl_vat)
                                                            : <span className="text-amber-500">Girilmedi</span>
                                                        }
                                                    </p>
                                                </div>
                                                <div>
                                                    <span className="text-slate-500">Komisyon</span>
                                                    <p className="font-medium">
                                                        {formatCurrency(calc.commission_amount_excl_vat)}
                                                        <span className="text-slate-400 text-xs ml-1">
                                                            ({formatPercent(calc.commission_rate)})
                                                        </span>
                                                    </p>
                                                </div>
                                                <div>
                                                    <span className="text-slate-500">Öd. KDV</span>
                                                    <p className="font-medium">{formatCurrency(calc.net_vat_payable)}</p>
                                                </div>
                                                <div>
                                                    <span className="text-slate-500">Kargo</span>
                                                    <p className="font-medium">{formatCurrency(calc.cargo_cost_excl_vat)}</p>
                                                </div>
                                                <div>
                                                    <span className="text-slate-500">Platform</span>
                                                    <p className="font-medium">{formatCurrency(calc.platform_fee_excl_vat)}</p>
                                                </div>
                                                <div>
                                                    <span className="text-slate-500">Toplam Maliyet</span>
                                                    <p className="font-medium">{formatCurrency(calc.total_cost)}</p>
                                                </div>
                                                <div>
                                                    <span className="text-slate-500">Net Kâr</span>
                                                    <p className={`font-bold ${getProfitColor(calc.net_profit)}`}>
                                                        {formatCurrency(calc.net_profit)}
                                                        <span className="text-xs ml-1">
                                                            ({formatPercent(calc.profit_margin_percent)})
                                                        </span>
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="bg-amber-50 rounded-lg p-4 text-sm text-amber-700">
                                            Bu kalem için henüz hesaplama yapılmamış.
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
