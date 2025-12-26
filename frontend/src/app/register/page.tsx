'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { authAPI } from '@/lib/api';

export default function RegisterPage() {
    const router = useRouter();
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        password_confirm: '',
        first_name: '',
        last_name: '',
        company_name: '',
    });
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (formData.password !== formData.password_confirm) {
            setError('Şifreler eşleşmiyor.');
            return;
        }

        setIsLoading(true);

        try {
            const response = await authAPI.register(formData);
            const { tokens } = response.data.data;

            localStorage.setItem('access_token', tokens.access);
            localStorage.setItem('refresh_token', tokens.refresh);

            router.push('/dashboard');
        } catch (err: any) {
            const errors = err.response?.data?.error?.details;
            if (errors) {
                const messages = Object.entries(errors)
                    .map(([key, value]) => `${key}: ${(value as string[]).join(', ')}`)
                    .join('\n');
                setError(messages);
            } else {
                setError('Kayıt başarısız. Lütfen bilgilerinizi kontrol edin.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-primary-900 flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-8">
                    <Link href="/" className="inline-flex items-center gap-2">
                        <div className="w-12 h-12 bg-primary-500 rounded-xl flex items-center justify-center">
                            <span className="text-white font-bold text-2xl">T</span>
                        </div>
                        <span className="text-white text-2xl font-semibold">Kârlılık Analizi</span>
                    </Link>
                </div>

                {/* Register Card */}
                <div className="bg-white rounded-2xl shadow-xl p-8">
                    <h1 className="text-2xl font-bold text-slate-800 text-center mb-6">
                        Hesap Oluştur
                    </h1>

                    {error && (
                        <div className="bg-danger-50 border border-danger-200 text-danger-600 rounded-lg p-3 mb-4 text-sm whitespace-pre-line">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="label">Ad</label>
                                <input
                                    type="text"
                                    name="first_name"
                                    className="input"
                                    value={formData.first_name}
                                    onChange={handleChange}
                                    placeholder="Ad"
                                    required
                                />
                            </div>
                            <div>
                                <label className="label">Soyad</label>
                                <input
                                    type="text"
                                    name="last_name"
                                    className="input"
                                    value={formData.last_name}
                                    onChange={handleChange}
                                    placeholder="Soyad"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="label">Şirket Adı (Opsiyonel)</label>
                            <input
                                type="text"
                                name="company_name"
                                className="input"
                                value={formData.company_name}
                                onChange={handleChange}
                                placeholder="Şirket Ltd. Şti."
                            />
                        </div>

                        <div>
                            <label className="label">Email</label>
                            <input
                                type="email"
                                name="email"
                                className="input"
                                value={formData.email}
                                onChange={handleChange}
                                placeholder="ornek@email.com"
                                required
                            />
                        </div>

                        <div>
                            <label className="label">Şifre</label>
                            <input
                                type="password"
                                name="password"
                                className="input"
                                value={formData.password}
                                onChange={handleChange}
                                placeholder="••••••••"
                                required
                                minLength={8}
                            />
                        </div>

                        <div>
                            <label className="label">Şifre Tekrar</label>
                            <input
                                type="password"
                                name="password_confirm"
                                className="input"
                                value={formData.password_confirm}
                                onChange={handleChange}
                                placeholder="••••••••"
                                required
                            />
                        </div>

                        <button
                            type="submit"
                            className="btn-primary w-full py-3"
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <div className="spinner" />
                                    Kayıt yapılıyor...
                                </span>
                            ) : (
                                'Kayıt Ol'
                            )}
                        </button>
                    </form>

                    <p className="text-center text-sm text-slate-500 mt-6">
                        Zaten hesabınız var mı?{' '}
                        <Link href="/login" className="text-primary-600 hover:underline font-medium">
                            Giriş Yap
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
