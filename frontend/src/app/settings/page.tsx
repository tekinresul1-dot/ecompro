'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/lib/auth-context';
import { authAPI, sellersAPI } from '@/lib/api';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Check, User, Key, Settings, Truck, Bell, List, Palette, Mail, Layers, CreditCard } from 'lucide-react';

type TabType = 'account' | 'trendyol' | 'general' | 'cargo' | 'alerts' | 'profit-list' | 'color' | 'email' | 'bulk' | 'payment';

const tabs = [
    { id: 'account' as const, label: 'Hesap Ayarları', icon: User },
    { id: 'trendyol' as const, label: 'Trendyol API Bilgileri', icon: Key },
    { id: 'general' as const, label: 'Genel Ayarlar', icon: Settings },
    { id: 'cargo' as const, label: 'Kargo Ayarları', icon: Truck },
    { id: 'alerts' as const, label: 'Uyarılar', icon: Bell },
    { id: 'profit-list' as const, label: 'Ürün Kârlılık Listesi', icon: List },
    { id: 'color' as const, label: 'Kâr Marjı Renklendirme', icon: Palette },
    { id: 'email' as const, label: 'Eposta Bildirim Ayarları', icon: Mail },
    { id: 'bulk' as const, label: 'Toplu İşlemler', icon: Layers },
    { id: 'payment' as const, label: 'Ödeme Bilgileri', icon: CreditCard },
];

export default function SettingsPage() {
    const { user, refreshUser } = useAuth();
    const queryClient = useQueryClient();
    const [activeTab, setActiveTab] = useState<TabType>('account');
    const [success, setSuccess] = useState('');
    const [error, setError] = useState('');

    // Profile form
    const [profileData, setProfileData] = useState({
        first_name: user?.first_name || '',
        last_name: user?.last_name || '',
        company_name: user?.company_name || '',
        phone_number: '',
    });

    // Password form
    const [passwordData, setPasswordData] = useState({
        old_password: '',
        new_password: '',
        new_password_confirm: '',
    });

    // General settings
    const [generalSettings, setGeneralSettings] = useState({
        default_vat_rate: user?.default_vat_rate?.toString() || '20',
        default_commission_rate: '12',
        currency: 'TRY',
    });

    // Cargo settings
    const [cargoSettings, setCargoSettings] = useState({
        default_cargo_cost: '15',
        cargo_vat_rate: '20',
        include_cargo_in_cost: true,
    });

    // Alert settings
    const [alertSettings, setAlertSettings] = useState({
        low_margin_threshold: '5',
        negative_margin_alert: true,
        daily_summary: true,
    });

    // Color settings
    const [colorSettings, setColorSettings] = useState({
        positive_color: '#22c55e',
        negative_color: '#ef4444',
        neutral_color: '#f59e0b',
        threshold_high: '20',
        threshold_low: '5',
    });

    // Email settings
    const [emailSettings, setEmailSettings] = useState({
        daily_report: true,
        weekly_report: false,
        monthly_report: true,
        loss_alert: true,
        sync_alert: true,
    });

    // Fetch sellers for Trendyol tab
    const { data: sellers } = useQuery({
        queryKey: ['sellers'],
        queryFn: () => sellersAPI.list(),
    });

    const sellerList = Array.isArray(sellers?.data)
        ? sellers.data
        : sellers?.data?.results || sellers?.data?.data || [];

    const profileMutation = useMutation({
        mutationFn: (data: any) => authAPI.updateProfile(data),
        onSuccess: () => {
            setSuccess('Ayarlar başarıyla kaydedildi.');
            refreshUser();
            setTimeout(() => setSuccess(''), 3000);
        },
        onError: (err: any) => {
            setError(err.response?.data?.error?.message || 'Kaydetme başarısız.');
        },
    });

    const passwordMutation = useMutation({
        mutationFn: (data: any) => authAPI.changePassword(data),
        onSuccess: () => {
            setSuccess('Şifre başarıyla değiştirildi.');
            setPasswordData({ old_password: '', new_password: '', new_password_confirm: '' });
            setTimeout(() => setSuccess(''), 3000);
        },
        onError: (err: any) => {
            setError(err.response?.data?.error?.message || 'Şifre değiştirilemedi.');
        },
    });

    const handleSave = () => {
        setError('');
        setSuccess('Ayarlar başarıyla kaydedildi.');
        setTimeout(() => setSuccess(''), 3000);
    };

    return (
        <DashboardLayout>
            <div className="flex gap-6">
                {/* Sidebar */}
                <div className="w-64 shrink-0">
                    <nav className="space-y-1">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`w-full flex items-center gap-3 px-4 py-3 text-left rounded-lg transition-colors ${activeTab === tab.id
                                        ? 'bg-primary-50 text-primary-600 font-medium border-r-4 border-primary-500'
                                        : 'text-slate-600 hover:bg-slate-50'
                                    }`}
                            >
                                <tab.icon className="w-5 h-5" />
                                {tab.label}
                            </button>
                        ))}
                    </nav>
                </div>

                {/* Content */}
                <div className="flex-1">
                    {/* Success/Error Messages */}
                    {success && (
                        <div className="bg-success-50 border border-success-200 text-success-600 rounded-lg p-3 mb-4 flex items-center gap-2">
                            <Check className="w-5 h-5" />
                            {success}
                        </div>
                    )}
                    {error && (
                        <div className="bg-danger-50 border border-danger-200 text-danger-600 rounded-lg p-3 mb-4">
                            {error}
                        </div>
                    )}

                    {/* Hesap Ayarları */}
                    {activeTab === 'account' && (
                        <div className="card">
                            <h2 className="text-xl font-semibold text-slate-800 mb-6">Hesap Ayarları</h2>

                            <div className="space-y-4">
                                <div className="grid md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="label">Ad</label>
                                        <input
                                            type="text"
                                            className="input"
                                            value={profileData.first_name}
                                            onChange={(e) => setProfileData((p) => ({ ...p, first_name: e.target.value }))}
                                        />
                                    </div>
                                    <div>
                                        <label className="label">Soyad</label>
                                        <input
                                            type="text"
                                            className="input"
                                            value={profileData.last_name}
                                            onChange={(e) => setProfileData((p) => ({ ...p, last_name: e.target.value }))}
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="label">Telefon</label>
                                    <input
                                        type="tel"
                                        className="input"
                                        value={profileData.phone_number}
                                        onChange={(e) => setProfileData((p) => ({ ...p, phone_number: e.target.value }))}
                                        placeholder="0532 123 45 67"
                                    />
                                </div>

                                <div>
                                    <label className="label">Email</label>
                                    <input
                                        type="email"
                                        className="input bg-slate-50"
                                        value={user?.email || ''}
                                        disabled
                                    />
                                    <p className="text-xs text-slate-400 mt-1">Email adresi değiştirilemez.</p>
                                </div>

                                <hr className="my-6" />

                                <h3 className="font-medium text-slate-700">Şifre Değiştir</h3>

                                <div>
                                    <label className="label">Mevcut Şifre</label>
                                    <input
                                        type="password"
                                        className="input"
                                        value={passwordData.old_password}
                                        onChange={(e) => setPasswordData((p) => ({ ...p, old_password: e.target.value }))}
                                    />
                                </div>

                                <div className="grid md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="label">Yeni Şifre</label>
                                        <input
                                            type="password"
                                            className="input"
                                            value={passwordData.new_password}
                                            onChange={(e) => setPasswordData((p) => ({ ...p, new_password: e.target.value }))}
                                        />
                                    </div>
                                    <div>
                                        <label className="label">Yeni Şifre (Tekrar)</label>
                                        <input
                                            type="password"
                                            className="input"
                                            value={passwordData.new_password_confirm}
                                            onChange={(e) => setPasswordData((p) => ({ ...p, new_password_confirm: e.target.value }))}
                                        />
                                    </div>
                                </div>

                                <button
                                    onClick={() => profileMutation.mutate(profileData)}
                                    className="btn-primary"
                                >
                                    Kaydet
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Trendyol API Bilgileri */}
                    {activeTab === 'trendyol' && (
                        <div className="card">
                            <h2 className="text-xl font-semibold text-slate-800 mb-6">Trendyol API Bilgileri</h2>

                            {sellerList.length === 0 ? (
                                <div className="text-center py-8">
                                    <p className="text-slate-500 mb-4">Henüz Trendyol hesabı eklenmemiş.</p>
                                    <a href="/sellers" className="btn-primary">
                                        Hesap Ekle
                                    </a>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {sellerList.map((seller: any) => (
                                        <div key={seller.id} className="border border-slate-200 rounded-lg p-4">
                                            <div className="flex items-center justify-between mb-3">
                                                <h3 className="font-medium text-slate-800">{seller.shop_name}</h3>
                                                <span className={`badge ${seller.is_active ? 'badge-success' : 'badge-danger'}`}>
                                                    {seller.is_active ? 'Aktif' : 'Pasif'}
                                                </span>
                                            </div>
                                            <div className="grid md:grid-cols-2 gap-4 text-sm">
                                                <div>
                                                    <span className="text-slate-500">Seller ID:</span>
                                                    <span className="ml-2 font-mono">{seller.seller_id}</span>
                                                </div>
                                                <div>
                                                    <span className="text-slate-500">Komisyon Oranı:</span>
                                                    <span className="ml-2">%{seller.default_commission_rate}</span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                    <a href="/sellers" className="btn-secondary inline-block">
                                        Hesapları Yönet
                                    </a>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Genel Ayarlar */}
                    {activeTab === 'general' && (
                        <div className="card">
                            <h2 className="text-xl font-semibold text-slate-800 mb-6">Genel Ayarlar</h2>

                            <div className="space-y-4">
                                <div>
                                    <label className="label">Varsayılan KDV Oranı (%)</label>
                                    <input
                                        type="number"
                                        className="input w-32"
                                        value={generalSettings.default_vat_rate}
                                        onChange={(e) => setGeneralSettings((p) => ({ ...p, default_vat_rate: e.target.value }))}
                                    />
                                </div>

                                <div>
                                    <label className="label">Varsayılan Komisyon Oranı (%)</label>
                                    <input
                                        type="number"
                                        className="input w-32"
                                        value={generalSettings.default_commission_rate}
                                        onChange={(e) => setGeneralSettings((p) => ({ ...p, default_commission_rate: e.target.value }))}
                                    />
                                </div>

                                <div>
                                    <label className="label">Para Birimi</label>
                                    <select
                                        className="input w-40"
                                        value={generalSettings.currency}
                                        onChange={(e) => setGeneralSettings((p) => ({ ...p, currency: e.target.value }))}
                                    >
                                        <option value="TRY">TRY (₺)</option>
                                        <option value="USD">USD ($)</option>
                                        <option value="EUR">EUR (€)</option>
                                    </select>
                                </div>

                                <button onClick={handleSave} className="btn-primary">
                                    Kaydet
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Kargo Ayarları */}
                    {activeTab === 'cargo' && (
                        <div className="card">
                            <h2 className="text-xl font-semibold text-slate-800 mb-6">Kargo Ayarları</h2>

                            <div className="space-y-4">
                                <div>
                                    <label className="label">Varsayılan Kargo Maliyeti (₺)</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        className="input w-32"
                                        value={cargoSettings.default_cargo_cost}
                                        onChange={(e) => setCargoSettings((p) => ({ ...p, default_cargo_cost: e.target.value }))}
                                    />
                                </div>

                                <div>
                                    <label className="label">Kargo KDV Oranı (%)</label>
                                    <input
                                        type="number"
                                        className="input w-32"
                                        value={cargoSettings.cargo_vat_rate}
                                        onChange={(e) => setCargoSettings((p) => ({ ...p, cargo_vat_rate: e.target.value }))}
                                    />
                                </div>

                                <label className="flex items-center gap-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={cargoSettings.include_cargo_in_cost}
                                        onChange={(e) => setCargoSettings((p) => ({ ...p, include_cargo_in_cost: e.target.checked }))}
                                        className="w-5 h-5 text-primary-500 rounded"
                                    />
                                    <span className="text-slate-700">Kargo maliyetini hesaplamalara dahil et</span>
                                </label>

                                <button onClick={handleSave} className="btn-primary">
                                    Kaydet
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Uyarılar */}
                    {activeTab === 'alerts' && (
                        <div className="card">
                            <h2 className="text-xl font-semibold text-slate-800 mb-6">Uyarı Ayarları</h2>

                            <div className="space-y-4">
                                <div>
                                    <label className="label">Düşük Marj Eşiği (%)</label>
                                    <input
                                        type="number"
                                        className="input w-32"
                                        value={alertSettings.low_margin_threshold}
                                        onChange={(e) => setAlertSettings((p) => ({ ...p, low_margin_threshold: e.target.value }))}
                                    />
                                    <p className="text-xs text-slate-400 mt-1">Bu değerin altındaki marjlar için uyarı gösterilir.</p>
                                </div>

                                <label className="flex items-center gap-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={alertSettings.negative_margin_alert}
                                        onChange={(e) => setAlertSettings((p) => ({ ...p, negative_margin_alert: e.target.checked }))}
                                        className="w-5 h-5 text-primary-500 rounded"
                                    />
                                    <span className="text-slate-700">Negatif marj uyarılarını göster</span>
                                </label>

                                <label className="flex items-center gap-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={alertSettings.daily_summary}
                                        onChange={(e) => setAlertSettings((p) => ({ ...p, daily_summary: e.target.checked }))}
                                        className="w-5 h-5 text-primary-500 rounded"
                                    />
                                    <span className="text-slate-700">Günlük özet bildirimi gönder</span>
                                </label>

                                <button onClick={handleSave} className="btn-primary">
                                    Kaydet
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Ürün Kârlılık Listesi */}
                    {activeTab === 'profit-list' && (
                        <div className="card">
                            <h2 className="text-xl font-semibold text-slate-800 mb-6">Ürün Kârlılık Listesi Ayarları</h2>

                            <div className="space-y-4">
                                <div>
                                    <label className="label">Sayfa başına ürün sayısı</label>
                                    <select className="input w-32">
                                        <option value="10">10</option>
                                        <option value="25">25</option>
                                        <option value="50">50</option>
                                        <option value="100">100</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="label">Varsayılan sıralama</label>
                                    <select className="input w-48">
                                        <option value="profit_desc">Kâr (Yüksekten Düşüğe)</option>
                                        <option value="profit_asc">Kâr (Düşükten Yükseğe)</option>
                                        <option value="margin_desc">Marj (Yüksekten Düşüğe)</option>
                                        <option value="sales_desc">Satış Adedi (Yüksekten)</option>
                                    </select>
                                </div>

                                <label className="flex items-center gap-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        defaultChecked
                                        className="w-5 h-5 text-primary-500 rounded"
                                    />
                                    <span className="text-slate-700">Maliyeti girilmemiş ürünleri göster</span>
                                </label>

                                <button onClick={handleSave} className="btn-primary">
                                    Kaydet
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Kâr Marjı Renklendirme */}
                    {activeTab === 'color' && (
                        <div className="card">
                            <h2 className="text-xl font-semibold text-slate-800 mb-6">Kâr Marjı Renklendirme</h2>

                            <div className="space-y-4">
                                <div className="grid md:grid-cols-3 gap-4">
                                    <div>
                                        <label className="label">Pozitif (Kâr)</label>
                                        <div className="flex items-center gap-2">
                                            <input
                                                type="color"
                                                value={colorSettings.positive_color}
                                                onChange={(e) => setColorSettings((p) => ({ ...p, positive_color: e.target.value }))}
                                                className="w-10 h-10 rounded cursor-pointer"
                                            />
                                            <input
                                                type="text"
                                                value={colorSettings.positive_color}
                                                onChange={(e) => setColorSettings((p) => ({ ...p, positive_color: e.target.value }))}
                                                className="input flex-1"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="label">Negatif (Zarar)</label>
                                        <div className="flex items-center gap-2">
                                            <input
                                                type="color"
                                                value={colorSettings.negative_color}
                                                onChange={(e) => setColorSettings((p) => ({ ...p, negative_color: e.target.value }))}
                                                className="w-10 h-10 rounded cursor-pointer"
                                            />
                                            <input
                                                type="text"
                                                value={colorSettings.negative_color}
                                                onChange={(e) => setColorSettings((p) => ({ ...p, negative_color: e.target.value }))}
                                                className="input flex-1"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="label">Nötr (Düşük Marj)</label>
                                        <div className="flex items-center gap-2">
                                            <input
                                                type="color"
                                                value={colorSettings.neutral_color}
                                                onChange={(e) => setColorSettings((p) => ({ ...p, neutral_color: e.target.value }))}
                                                className="w-10 h-10 rounded cursor-pointer"
                                            />
                                            <input
                                                type="text"
                                                value={colorSettings.neutral_color}
                                                onChange={(e) => setColorSettings((p) => ({ ...p, neutral_color: e.target.value }))}
                                                className="input flex-1"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <hr className="my-4" />

                                <div className="grid md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="label">Yüksek marj eşiği (%)</label>
                                        <input
                                            type="number"
                                            className="input w-32"
                                            value={colorSettings.threshold_high}
                                            onChange={(e) => setColorSettings((p) => ({ ...p, threshold_high: e.target.value }))}
                                        />
                                        <p className="text-xs text-slate-400 mt-1">Bu değerin üstü yeşil gösterilir.</p>
                                    </div>
                                    <div>
                                        <label className="label">Düşük marj eşiği (%)</label>
                                        <input
                                            type="number"
                                            className="input w-32"
                                            value={colorSettings.threshold_low}
                                            onChange={(e) => setColorSettings((p) => ({ ...p, threshold_low: e.target.value }))}
                                        />
                                        <p className="text-xs text-slate-400 mt-1">Bu değerin altı sarı gösterilir.</p>
                                    </div>
                                </div>

                                <button onClick={handleSave} className="btn-primary">
                                    Kaydet
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Eposta Bildirim Ayarları */}
                    {activeTab === 'email' && (
                        <div className="card">
                            <h2 className="text-xl font-semibold text-slate-800 mb-6">Eposta Bildirim Ayarları</h2>

                            <div className="space-y-4">
                                <label className="flex items-center gap-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={emailSettings.daily_report}
                                        onChange={(e) => setEmailSettings((p) => ({ ...p, daily_report: e.target.checked }))}
                                        className="w-5 h-5 text-primary-500 rounded"
                                    />
                                    <span className="text-slate-700">Günlük kâr raporu gönder</span>
                                </label>

                                <label className="flex items-center gap-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={emailSettings.weekly_report}
                                        onChange={(e) => setEmailSettings((p) => ({ ...p, weekly_report: e.target.checked }))}
                                        className="w-5 h-5 text-primary-500 rounded"
                                    />
                                    <span className="text-slate-700">Haftalık özet raporu gönder</span>
                                </label>

                                <label className="flex items-center gap-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={emailSettings.monthly_report}
                                        onChange={(e) => setEmailSettings((p) => ({ ...p, monthly_report: e.target.checked }))}
                                        className="w-5 h-5 text-primary-500 rounded"
                                    />
                                    <span className="text-slate-700">Aylık analiz raporu gönder</span>
                                </label>

                                <label className="flex items-center gap-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={emailSettings.loss_alert}
                                        onChange={(e) => setEmailSettings((p) => ({ ...p, loss_alert: e.target.checked }))}
                                        className="w-5 h-5 text-primary-500 rounded"
                                    />
                                    <span className="text-slate-700">Zarar uyarısı gönder</span>
                                </label>

                                <label className="flex items-center gap-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={emailSettings.sync_alert}
                                        onChange={(e) => setEmailSettings((p) => ({ ...p, sync_alert: e.target.checked }))}
                                        className="w-5 h-5 text-primary-500 rounded"
                                    />
                                    <span className="text-slate-700">Senkronizasyon hata bildirimi gönder</span>
                                </label>

                                <button onClick={handleSave} className="btn-primary">
                                    Kaydet
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Toplu İşlemler */}
                    {activeTab === 'bulk' && (
                        <div className="card">
                            <h2 className="text-xl font-semibold text-slate-800 mb-6">Toplu İşlemler</h2>

                            <div className="space-y-6">
                                <div className="border border-slate-200 rounded-lg p-4">
                                    <h3 className="font-medium text-slate-800 mb-2">Maliyet Toplu Güncelleme</h3>
                                    <p className="text-sm text-slate-500 mb-3">
                                        Excel dosyası ile ürün maliyetlerini toplu olarak güncelleyin.
                                    </p>
                                    <div className="flex gap-3">
                                        <button className="btn-secondary">Şablon İndir</button>
                                        <button className="btn-primary">Excel Yükle</button>
                                    </div>
                                </div>

                                <div className="border border-slate-200 rounded-lg p-4">
                                    <h3 className="font-medium text-slate-800 mb-2">Veri Dışa Aktarma</h3>
                                    <p className="text-sm text-slate-500 mb-3">
                                        Tüm verilerinizi Excel formatında indirin.
                                    </p>
                                    <div className="flex gap-3">
                                        <button className="btn-secondary">Ürünleri İndir</button>
                                        <button className="btn-secondary">Siparişleri İndir</button>
                                        <button className="btn-secondary">Hesaplamaları İndir</button>
                                    </div>
                                </div>

                                <div className="border border-slate-200 rounded-lg p-4">
                                    <h3 className="font-medium text-slate-800 mb-2">Toplu Hesaplama</h3>
                                    <p className="text-sm text-slate-500 mb-3">
                                        Tüm siparişler için kâr hesaplamalarını yeniden çalıştırın.
                                    </p>
                                    <button className="btn-primary">Hesaplamaları Yenile</button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Ödeme Bilgileri */}
                    {activeTab === 'payment' && (
                        <div className="card">
                            <h2 className="text-xl font-semibold text-slate-800 mb-6">Ödeme Bilgileri</h2>

                            <div className="bg-slate-50 rounded-lg p-6 text-center">
                                <div className="text-4xl mb-4">💳</div>
                                <h3 className="font-medium text-slate-800 mb-2">Ücretsiz Plan</h3>
                                <p className="text-slate-500 mb-4">
                                    Şu anda ücretsiz plan kullanıyorsunuz. Premium özelliklere erişmek için planınızı yükseltin.
                                </p>
                                <button className="btn-primary">Planları Görüntüle</button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </DashboardLayout>
    );
}
