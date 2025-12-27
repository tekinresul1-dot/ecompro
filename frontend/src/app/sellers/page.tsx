'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sellersAPI } from '@/lib/api';
import { formatDateTime, getSyncStatusBadge } from '@/lib/utils';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Plus, RefreshCw, Trash2, Settings, Check, X } from 'lucide-react';

export default function SellersPage() {
    const queryClient = useQueryClient();
    const [showAddModal, setShowAddModal] = useState(false);
    const [selectedSeller, setSelectedSeller] = useState<any>(null);

    // Fetch sellers
    const { data: sellers, isLoading } = useQuery({
        queryKey: ['sellers'],
        queryFn: () => sellersAPI.list(),
    });

    // Sync mutation
    const syncMutation = useMutation({
        mutationFn: (id: number) => sellersAPI.triggerSync(id, 'incremental'),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['sellers'] });
        },
    });

    // Delete mutation
    const deleteMutation = useMutation({
        mutationFn: (id: number) => sellersAPI.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['sellers'] });
        },
    });

    // Handle different API response formats
    const sellerData = sellers?.data;
    const sellerList = Array.isArray(sellerData)
        ? sellerData
        : sellerData?.results || sellerData?.data || [];

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-bold text-slate-800">Satıcı Hesapları</h1>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="btn-primary flex items-center gap-2"
                    >
                        <Plus className="w-4 h-4" />
                        Hesap Ekle
                    </button>
                </div>

                {/* Sellers Grid */}
                {isLoading ? (
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {[1, 2].map((i) => (
                            <div key={i} className="card animate-pulse">
                                <div className="h-6 w-32 bg-slate-200 rounded mb-4" />
                                <div className="h-4 w-48 bg-slate-200 rounded" />
                            </div>
                        ))}
                    </div>
                ) : sellerList.length === 0 ? (
                    <div className="card text-center py-12">
                        <div className="text-4xl mb-4">🏪</div>
                        <h3 className="text-lg font-semibold text-slate-800 mb-2">
                            Henüz satıcı hesabı eklenmemiş
                        </h3>
                        <p className="text-slate-500 mb-4">
                            Trendyol satıcı hesabınızı ekleyerek siparişlerinizi senkronize edin.
                        </p>
                        <button
                            onClick={() => setShowAddModal(true)}
                            className="btn-primary"
                        >
                            İlk Hesabı Ekle
                        </button>
                    </div>
                ) : (
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {sellerList.map((seller: any) => {
                            const statusBadge = getSyncStatusBadge(seller.sync_status);

                            return (
                                <div key={seller.id} className="card hover:shadow-md transition-shadow">
                                    {/* Header */}
                                    <div className="flex items-start justify-between mb-4">
                                        <div>
                                            <h3 className="font-semibold text-slate-800">{seller.shop_name}</h3>
                                            <p className="text-sm text-slate-500">ID: {seller.seller_id}</p>
                                        </div>
                                        <span className={statusBadge.class}>{statusBadge.label}</span>
                                    </div>

                                    {/* Stats */}
                                    <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                                        <div>
                                            <span className="text-slate-500">Ürün Sayısı</span>
                                            <p className="font-medium text-slate-800">{seller.product_count || 0}</p>
                                        </div>
                                        <div>
                                            <span className="text-slate-500">Sipariş Sayısı</span>
                                            <p className="font-medium text-slate-800">{seller.order_count || 0}</p>
                                        </div>
                                    </div>

                                    {/* Last Sync */}
                                    <div className="text-sm text-slate-500 mb-4">
                                        Son Senkronizasyon: {formatDateTime(seller.last_sync_at) || 'Henüz yok'}
                                    </div>

                                    {/* Actions */}
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => syncMutation.mutate(seller.id)}
                                            disabled={syncMutation.isPending}
                                            className="flex-1 btn-secondary flex items-center justify-center gap-2 py-2"
                                        >
                                            <RefreshCw className={`w-4 h-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
                                            Senkronize Et
                                        </button>
                                        <button
                                            onClick={() => setSelectedSeller(seller)}
                                            className="btn-secondary p-2"
                                        >
                                            <Settings className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => {
                                                if (confirm('Bu satıcı hesabını silmek istediğinize emin misiniz?')) {
                                                    deleteMutation.mutate(seller.id);
                                                }
                                            }}
                                            className="btn-secondary p-2 hover:bg-danger-50 hover:text-danger-500"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Add Modal */}
                {showAddModal && (
                    <AddSellerModal onClose={() => setShowAddModal(false)} />
                )}
            </div>
        </DashboardLayout>
    );
}

function AddSellerModal({ onClose }: { onClose: () => void }) {
    const queryClient = useQueryClient();
    const [formData, setFormData] = useState({
        seller_id: '',
        api_key: '',
        api_secret: '',
        shop_name: '',
        default_commission_rate: '12',
    });
    const [error, setError] = useState('');

    const createMutation = useMutation({
        mutationFn: (data: any) => sellersAPI.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['sellers'] });
            onClose();
        },
        onError: (err: any) => {
            console.error('Create seller error:', err.response?.data);
            // Try to extract detailed error message
            const errorData = err.response?.data;
            let errorMessage = 'Hesap eklenemedi.';

            if (errorData?.error?.message) {
                errorMessage = errorData.error.message;
            } else if (errorData?.detail) {
                errorMessage = errorData.detail;
            } else if (errorData?.message) {
                errorMessage = errorData.message;
            } else if (typeof errorData === 'object') {
                // Handle field-level errors
                const fieldErrors = Object.entries(errorData)
                    .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(', ') : errors}`)
                    .join('; ');
                if (fieldErrors) errorMessage = fieldErrors;
            }

            setError(errorMessage);
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        createMutation.mutate({
            ...formData,
            default_commission_rate: parseFloat(formData.default_commission_rate),
        });
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
                <div className="p-6 border-b border-slate-200">
                    <h2 className="text-xl font-semibold text-slate-800">Satıcı Hesabı Ekle</h2>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    {error && (
                        <div className="bg-danger-50 border border-danger-200 text-danger-600 rounded-lg p-3 text-sm">
                            {error}
                        </div>
                    )}

                    <div>
                        <label className="label">Mağaza Adı</label>
                        <input
                            type="text"
                            className="input"
                            value={formData.shop_name}
                            onChange={(e) => setFormData((p) => ({ ...p, shop_name: e.target.value }))}
                            placeholder="Örn: Tekin Moda"
                            required
                        />
                    </div>

                    <div>
                        <label className="label">Seller ID</label>
                        <input
                            type="text"
                            className="input"
                            value={formData.seller_id}
                            onChange={(e) => setFormData((p) => ({ ...p, seller_id: e.target.value }))}
                            placeholder="Trendyol Satıcı ID"
                            required
                        />
                    </div>

                    <div>
                        <label className="label">API Key</label>
                        <input
                            type="text"
                            className="input"
                            value={formData.api_key}
                            onChange={(e) => setFormData((p) => ({ ...p, api_key: e.target.value }))}
                            placeholder="API anahtarı"
                            required
                        />
                    </div>

                    <div>
                        <label className="label">API Secret</label>
                        <input
                            type="password"
                            className="input"
                            value={formData.api_secret}
                            onChange={(e) => setFormData((p) => ({ ...p, api_secret: e.target.value }))}
                            placeholder="API şifresi"
                            required
                        />
                    </div>

                    <div>
                        <label className="label">Varsayılan Komisyon Oranı (%)</label>
                        <input
                            type="number"
                            step="0.01"
                            className="input"
                            value={formData.default_commission_rate}
                            onChange={(e) => setFormData((p) => ({ ...p, default_commission_rate: e.target.value }))}
                            required
                        />
                    </div>

                    <div className="flex gap-3 pt-4">
                        <button type="button" onClick={onClose} className="flex-1 btn-secondary">
                            İptal
                        </button>
                        <button
                            type="submit"
                            disabled={createMutation.isPending}
                            className="flex-1 btn-primary"
                        >
                            {createMutation.isPending ? 'Ekleniyor...' : 'Hesap Ekle'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
