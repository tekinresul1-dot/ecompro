'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { productsAPI, sellersAPI } from '@/lib/api';
import { formatCurrency, formatPercent } from '@/lib/utils';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Search, Upload, Download, Edit2, Check, X } from 'lucide-react';

export default function ProductsPage() {
    const queryClient = useQueryClient();
    const [search, setSearch] = useState('');
    const [selectedSeller, setSelectedSeller] = useState<number | undefined>();
    const [showWithoutCost, setShowWithoutCost] = useState(false);
    const [editingProduct, setEditingProduct] = useState<number | null>(null);
    const [editCost, setEditCost] = useState('');

    // Fetch sellers
    const { data: sellers } = useQuery({
        queryKey: ['sellers'],
        queryFn: () => sellersAPI.list(),
    });

    // Fetch products
    const { data: products, isLoading } = useQuery({
        queryKey: ['products', selectedSeller, search, showWithoutCost],
        queryFn: () =>
            showWithoutCost
                ? productsAPI.getWithoutCost({ seller_account: selectedSeller, search })
                : productsAPI.list({ seller_account: selectedSeller, search }),
    });

    // Update cost mutation
    const updateCostMutation = useMutation({
        mutationFn: ({ id, cost }: { id: number; cost: number }) =>
            productsAPI.updateCost(id, { product_cost_excl_vat: cost }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['products'] });
            setEditingProduct(null);
        },
    });

    // Export handler
    const handleExport = async () => {
        const response = await productsAPI.export(selectedSeller);
        const blob = new Blob([response.data], {
            type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `products_${new Date().toISOString().split('T')[0]}.xlsx`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const productList = products?.data?.results || products?.data || [];

    // Handle sellers data - could be array directly or nested
    const sellerList = Array.isArray(sellers?.data)
        ? sellers.data
        : sellers?.data?.results || sellers?.data?.data || [];

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <h1 className="text-2xl font-bold text-slate-800">Ürünler</h1>

                    <div className="flex flex-wrap gap-3">
                        <button onClick={handleExport} className="btn-secondary flex items-center gap-2">
                            <Download className="w-4 h-4" />
                            Excel İndir
                        </button>
                        <button className="btn-primary flex items-center gap-2">
                            <Upload className="w-4 h-4" />
                            Toplu Yükle
                        </button>
                    </div>
                </div>

                {/* Filters */}
                <div className="card">
                    <div className="flex flex-wrap gap-4">
                        <div className="flex-1 min-w-[200px]">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                                <input
                                    type="text"
                                    className="input pl-10"
                                    placeholder="Barkod veya ürün adı ara..."
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                />
                            </div>
                        </div>

                        <select
                            className="input w-48"
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

                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={showWithoutCost}
                                onChange={(e) => setShowWithoutCost(e.target.checked)}
                                className="w-4 h-4 text-primary-500 rounded"
                            />
                            <span className="text-sm text-slate-600">Maliyetsiz Ürünler</span>
                        </label>
                    </div>
                </div>

                {/* Products Table */}
                <div className="card p-0">
                    <div className="table-container">
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Barkod</th>
                                    <th>Ürün Adı</th>
                                    <th className="text-right">Maliyet (KDV Hariç)</th>
                                    <th className="text-right">KDV Oranı</th>
                                    <th className="text-right">Komisyon</th>
                                    <th className="text-right">Satış Adedi</th>
                                    <th className="w-20"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {isLoading ? (
                                    <tr>
                                        <td colSpan={7} className="text-center py-8">
                                            <div className="spinner mx-auto" />
                                        </td>
                                    </tr>
                                ) : productList.length === 0 ? (
                                    <tr>
                                        <td colSpan={7} className="text-center py-8 text-slate-400">
                                            Ürün bulunamadı
                                        </td>
                                    </tr>
                                ) : (
                                    productList.map((product: any) => (
                                        <tr key={product.id}>
                                            <td className="font-mono text-sm">{product.barcode}</td>
                                            <td>
                                                <div className="max-w-xs truncate">{product.title}</div>
                                            </td>
                                            <td className="text-right">
                                                {editingProduct === product.id ? (
                                                    <div className="flex items-center justify-end gap-2">
                                                        <input
                                                            type="number"
                                                            step="0.01"
                                                            className="input w-24 text-right py-1"
                                                            value={editCost}
                                                            onChange={(e) => setEditCost(e.target.value)}
                                                            autoFocus
                                                        />
                                                        <button
                                                            onClick={() => {
                                                                updateCostMutation.mutate({
                                                                    id: product.id,
                                                                    cost: parseFloat(editCost),
                                                                });
                                                            }}
                                                            className="p-1 text-success-500 hover:bg-success-50 rounded"
                                                        >
                                                            <Check className="w-4 h-4" />
                                                        </button>
                                                        <button
                                                            onClick={() => setEditingProduct(null)}
                                                            className="p-1 text-slate-400 hover:bg-slate-100 rounded"
                                                        >
                                                            <X className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                ) : product.has_cost_data ? (
                                                    formatCurrency(product.product_cost_excl_vat)
                                                ) : (
                                                    <span className="text-amber-500">Girilmedi</span>
                                                )}
                                            </td>
                                            <td className="text-right">{formatPercent(product.sales_vat_rate)}</td>
                                            <td className="text-right">{formatPercent(product.commission_rate)}</td>
                                            <td className="text-right">{product.total_sales_quantity || 0}</td>
                                            <td>
                                                {editingProduct !== product.id && (
                                                    <button
                                                        onClick={() => {
                                                            setEditingProduct(product.id);
                                                            setEditCost(product.product_cost_excl_vat || '');
                                                        }}
                                                        className="p-2 text-slate-400 hover:text-primary-500 hover:bg-primary-50 rounded"
                                                    >
                                                        <Edit2 className="w-4 h-4" />
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
