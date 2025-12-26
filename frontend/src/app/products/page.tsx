'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { productsAPI, sellersAPI } from '@/lib/api';
import { formatCurrency, formatPercent } from '@/lib/utils';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Search, Upload, Download, RefreshCw, FileSpreadsheet, Check, X, ChevronDown, ChevronUp, Filter, Loader2 } from 'lucide-react';

export default function ProductsPage() {
    const queryClient = useQueryClient();
    const [search, setSearch] = useState('');
    const [selectedSeller, setSelectedSeller] = useState<number | undefined>();
    const [editingProduct, setEditingProduct] = useState<number | null>(null);
    const [editCost, setEditCost] = useState('');
    const [editVatRate, setEditVatRate] = useState('18');
    const [sortField, setSortField] = useState<string>('');
    const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
    const [showVariants, setShowVariants] = useState<number | null>(null);

    // Fetch sellers
    const { data: sellers } = useQuery({
        queryKey: ['sellers'],
        queryFn: () => sellersAPI.list(),
    });

    // Fetch products
    const { data: products, isLoading, refetch, isFetching } = useQuery({
        queryKey: ['products', selectedSeller, search],
        queryFn: () => productsAPI.list({ seller_account: selectedSeller, search }),
    });

    // Update cost mutation
    const updateCostMutation = useMutation({
        mutationFn: ({ id, cost, vatRate }: { id: number; cost: number; vatRate: number }) =>
            productsAPI.updateCost(id, {
                product_cost_excl_vat: cost / (1 + vatRate / 100), // Convert from VAT included to excluded
                purchase_vat_rate: vatRate
            }),
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
        a.download = `urun_ayarlari_${new Date().toISOString().split('T')[0]}.xlsx`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const productList = products?.data?.results || products?.data || [];

    // Handle sellers data
    const sellerList = Array.isArray(sellers?.data)
        ? sellers.data
        : sellers?.data?.results || sellers?.data?.data || [];

    // Sort products
    const sortedProducts = [...productList].sort((a: any, b: any) => {
        if (!sortField) return 0;
        const aVal = a[sortField];
        const bVal = b[sortField];
        if (sortDir === 'asc') return aVal > bVal ? 1 : -1;
        return aVal < bVal ? 1 : -1;
    });

    // Handle sort
    const handleSort = (field: string) => {
        if (sortField === field) {
            setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDir('asc');
        }
    };

    // Sort indicator
    const SortIcon = ({ field }: { field: string }) => {
        if (sortField !== field) return null;
        return sortDir === 'asc' ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />;
    };

    // VAT rate options
    const vatRates = [1, 10, 18, 20];

    return (
        <DashboardLayout>
            <div className="space-y-4">
                {/* Header */}
                <div className="bg-gradient-to-r from-slate-700 to-slate-800 rounded-2xl px-6 py-4 flex items-center justify-between">
                    <h1 className="text-xl font-semibold text-white">Ürün Ayarları</h1>

                    <div className="flex items-center gap-2">
                        {/* Zoom controls */}
                        <button className="bg-slate-600 hover:bg-slate-500 text-white px-3 py-1.5 rounded text-sm">
                            A+
                        </button>
                        <span className="bg-white text-slate-700 px-3 py-1.5 rounded text-sm font-medium">
                            70%
                        </span>
                        <button className="bg-slate-600 hover:bg-slate-500 text-white px-3 py-1.5 rounded text-sm">
                            A-
                        </button>
                        <button className="bg-slate-600 hover:bg-slate-500 text-white p-1.5 rounded">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-wrap items-center justify-between gap-4">
                    {/* Search and Filter */}
                    <div className="flex items-center gap-3">
                        <select
                            className="bg-white border border-slate-200 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
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

                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <input
                                type="text"
                                className="bg-white border border-slate-200 rounded-lg pl-10 pr-4 py-2 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-primary-500"
                                placeholder="Barkod veya ürün adı ara..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                            />
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => refetch()}
                            className="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                        >
                            {isFetching ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                            Verileri Güncelle
                        </button>

                        <button
                            onClick={handleExport}
                            className="bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                        >
                            <FileSpreadsheet className="w-4 h-4" />
                            Excel Dosyasını İndir
                        </button>

                        <button className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2">
                            <Download className="w-4 h-4" />
                            Casel ile toplu aktarım
                        </button>

                        <button className="bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2">
                            <Upload className="w-4 h-4" />
                            XML Yükle
                        </button>
                    </div>
                </div>

                {/* Products Table */}
                <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-slate-50 border-b border-slate-200">
                                <tr>
                                    <th className="px-4 py-3 text-left font-medium text-slate-600 w-8">
                                        Varyantları
                                    </th>
                                    <th
                                        className="px-4 py-3 text-left font-medium text-slate-600 cursor-pointer hover:text-slate-800"
                                        onClick={() => handleSort('title')}
                                    >
                                        <div className="flex items-center gap-1">
                                            Ürün Bilgisi
                                            <SortIcon field="title" />
                                        </div>
                                    </th>
                                    <th
                                        className="px-4 py-3 text-left font-medium text-slate-600 cursor-pointer hover:text-slate-800"
                                        onClick={() => handleSort('barcode')}
                                    >
                                        <div className="flex items-center gap-1">
                                            Barkod
                                            <SortIcon field="barcode" />
                                        </div>
                                    </th>
                                    <th className="px-4 py-3 text-center font-medium text-slate-600">
                                        Ürün Maliyeti (KDV Dahil)
                                    </th>
                                    <th className="px-4 py-3 text-center font-medium text-slate-600">
                                        Maliyet KDV Oranı
                                    </th>
                                    <th
                                        className="px-4 py-3 text-center font-medium text-slate-600 cursor-pointer hover:text-slate-800"
                                        onClick={() => handleSort('desi')}
                                    >
                                        <div className="flex items-center justify-center gap-1">
                                            Desi
                                            <SortIcon field="desi" />
                                        </div>
                                    </th>
                                    <th className="px-4 py-3 text-left font-medium text-slate-600">
                                        Marka
                                    </th>
                                    <th className="px-4 py-3 text-left font-medium text-slate-600">
                                        Model Kodu
                                    </th>
                                    <th className="px-4 py-3 text-left font-medium text-slate-600">
                                        Renk
                                    </th>
                                    <th className="px-4 py-3 text-left font-medium text-slate-600">
                                        Beden
                                    </th>
                                    <th className="px-4 py-3 text-center font-medium text-slate-600">
                                        Stok(Adet)
                                    </th>
                                    <th className="px-4 py-3 text-center font-medium text-slate-600">
                                        İade Oranı
                                    </th>
                                    <th className="px-4 py-3 text-center font-medium text-slate-600">
                                        Bugün Kargoda
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {isLoading ? (
                                    <tr>
                                        <td colSpan={13} className="text-center py-12">
                                            <Loader2 className="w-8 h-8 animate-spin text-primary-500 mx-auto" />
                                        </td>
                                    </tr>
                                ) : sortedProducts.length === 0 ? (
                                    <tr>
                                        <td colSpan={13} className="text-center py-12 text-slate-400">
                                            Ürün bulunamadı
                                        </td>
                                    </tr>
                                ) : (
                                    sortedProducts.map((product: any, index: number) => (
                                        <tr
                                            key={product.id}
                                            className={`border-b border-slate-100 hover:bg-slate-50 ${index % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'
                                                }`}
                                        >
                                            {/* Variants Toggle */}
                                            <td className="px-4 py-3">
                                                {product.has_variants ? (
                                                    <button
                                                        onClick={() => setShowVariants(showVariants === product.id ? null : product.id)}
                                                        className={`w-6 h-6 rounded flex items-center justify-center text-xs font-medium ${showVariants === product.id
                                                                ? 'bg-primary-500 text-white'
                                                                : 'bg-orange-100 text-orange-600'
                                                            }`}
                                                    >
                                                        {product.variant_count || 'V'}
                                                    </button>
                                                ) : (
                                                    <span className="text-slate-400">-</span>
                                                )}
                                            </td>

                                            {/* Product Info */}
                                            <td className="px-4 py-3">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-12 h-12 bg-slate-100 rounded-lg overflow-hidden flex-shrink-0">
                                                        {product.image_url ? (
                                                            <img
                                                                src={product.image_url}
                                                                alt={product.title}
                                                                className="w-full h-full object-cover"
                                                            />
                                                        ) : (
                                                            <div className="w-full h-full flex items-center justify-center text-slate-400">
                                                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                                </svg>
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div className="min-w-0">
                                                        <a
                                                            href={product.product_url || '#'}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="font-medium text-primary-600 hover:underline block truncate max-w-[200px]"
                                                        >
                                                            {product.title}
                                                        </a>
                                                        <p className="text-xs text-slate-500 truncate">
                                                            {product.category || 'Kategori'}
                                                        </p>
                                                        <p className="text-xs text-slate-400">
                                                            Beden: <span className="text-slate-600">{product.size || 'Standart'}</span>
                                                        </p>
                                                    </div>
                                                </div>
                                            </td>

                                            {/* Barcode */}
                                            <td className="px-4 py-3 font-mono text-xs text-slate-600">
                                                {product.barcode}
                                            </td>

                                            {/* Cost Input */}
                                            <td className="px-4 py-3">
                                                <div className="flex items-center justify-center gap-1">
                                                    {editingProduct === product.id ? (
                                                        <>
                                                            <input
                                                                type="number"
                                                                step="0.01"
                                                                className="w-20 px-2 py-1 border border-primary-300 rounded text-center text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                                                                value={editCost}
                                                                onChange={(e) => setEditCost(e.target.value)}
                                                                autoFocus
                                                            />
                                                            <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">TRY</span>
                                                            <button
                                                                onClick={() => {
                                                                    updateCostMutation.mutate({
                                                                        id: product.id,
                                                                        cost: parseFloat(editCost),
                                                                        vatRate: parseInt(editVatRate),
                                                                    });
                                                                }}
                                                                className="p-1 text-emerald-500 hover:bg-emerald-50 rounded"
                                                            >
                                                                <Check className="w-4 h-4" />
                                                            </button>
                                                            <button
                                                                onClick={() => setEditingProduct(null)}
                                                                className="p-1 text-slate-400 hover:bg-slate-100 rounded"
                                                            >
                                                                <X className="w-4 h-4" />
                                                            </button>
                                                        </>
                                                    ) : (
                                                        <button
                                                            onClick={() => {
                                                                setEditingProduct(product.id);
                                                                const costWithVat = product.product_cost_excl_vat
                                                                    ? (product.product_cost_excl_vat * (1 + (product.purchase_vat_rate || 18) / 100)).toFixed(2)
                                                                    : '';
                                                                setEditCost(costWithVat);
                                                                setEditVatRate(product.purchase_vat_rate?.toString() || '18');
                                                            }}
                                                            className={`px-3 py-1 border rounded text-sm transition-colors ${product.has_cost_data
                                                                    ? 'border-slate-200 bg-white text-slate-700 hover:border-primary-300'
                                                                    : 'border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100'
                                                                }`}
                                                        >
                                                            {product.has_cost_data
                                                                ? formatCurrency(product.product_cost_excl_vat * (1 + (product.purchase_vat_rate || 18) / 100))
                                                                : '---'
                                                            }
                                                        </button>
                                                    )}
                                                </div>
                                            </td>

                                            {/* VAT Rate */}
                                            <td className="px-4 py-3">
                                                <div className="flex justify-center">
                                                    {editingProduct === product.id ? (
                                                        <select
                                                            value={editVatRate}
                                                            onChange={(e) => setEditVatRate(e.target.value)}
                                                            className="px-2 py-1 border border-primary-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                                                        >
                                                            {vatRates.map(rate => (
                                                                <option key={rate} value={rate}>{rate}%</option>
                                                            ))}
                                                        </select>
                                                    ) : (
                                                        <span className="px-3 py-1 bg-slate-100 rounded text-sm text-slate-600">
                                                            {product.purchase_vat_rate || 18}%
                                                        </span>
                                                    )}
                                                </div>
                                            </td>

                                            {/* Desi */}
                                            <td className="px-4 py-3 text-center">
                                                <span className={`px-2 py-0.5 rounded text-sm ${product.desi ? 'bg-blue-50 text-blue-600' : 'text-slate-400'
                                                    }`}>
                                                    {product.desi || '---'}
                                                </span>
                                            </td>

                                            {/* Brand */}
                                            <td className="px-4 py-3 text-slate-600">
                                                {product.brand || 'Sohvaldi'}
                                            </td>

                                            {/* Model Code */}
                                            <td className="px-4 py-3 font-mono text-xs text-slate-600">
                                                {product.model_code || product.barcode?.slice(-6) || '---'}
                                            </td>

                                            {/* Color */}
                                            <td className="px-4 py-3 text-slate-600">
                                                {product.color || '---'}
                                            </td>

                                            {/* Size */}
                                            <td className="px-4 py-3 text-slate-600">
                                                {product.size || 'Standart'}
                                            </td>

                                            {/* Stock */}
                                            <td className="px-4 py-3 text-center">
                                                <span className={`font-medium ${product.stock > 0 ? 'text-slate-800' : 'text-red-500'
                                                    }`}>
                                                    {product.stock || 0}
                                                </span>
                                            </td>

                                            {/* Return Rate */}
                                            <td className="px-4 py-3 text-center">
                                                {product.return_rate ? (
                                                    <span className={`px-2 py-0.5 rounded text-sm ${product.return_rate > 10
                                                            ? 'bg-red-50 text-red-600'
                                                            : 'bg-emerald-50 text-emerald-600'
                                                        }`}>
                                                        Varyasyonlar ({product.variant_count || 0})
                                                    </span>
                                                ) : (
                                                    <span className="text-slate-400">---</span>
                                                )}
                                            </td>

                                            {/* Shipped Today */}
                                            <td className="px-4 py-3 text-center">
                                                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-sm ${product.shipped_today
                                                        ? 'bg-emerald-50 text-emerald-600'
                                                        : 'bg-slate-100 text-slate-500'
                                                    }`}>
                                                    <span className={`w-2 h-2 rounded-full ${product.shipped_today ? 'bg-emerald-500' : 'bg-slate-400'
                                                        }`}></span>
                                                    {product.shipped_today ? 'Kargoda' : 'Kargoda'}
                                                </span>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Pagination */}
                    <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200 text-sm text-slate-500">
                        <div className="flex gap-4">
                            <span>Geçerli sayfa: <strong className="text-slate-700">1</strong></span>
                            <span>Toplam kayıt sayısı: <strong className="text-primary-600">{sortedProducts.length}</strong></span>
                        </div>
                        <span>Sayfa başına gösterilen kayıt sayısı: <strong>50</strong></span>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
