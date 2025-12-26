import Link from 'next/link';

export default function Home() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-primary-900">
            <div className="container mx-auto px-4 py-16">
                {/* Header */}
                <nav className="flex justify-between items-center mb-16">
                    <div className="flex items-center gap-2">
                        <div className="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center">
                            <span className="text-white font-bold text-xl">T</span>
                        </div>
                        <span className="text-white text-xl font-semibold">Trendyol Kârlılık</span>
                    </div>
                    <div className="flex gap-4">
                        <Link href="/login" className="text-slate-300 hover:text-white transition-colors">
                            Giriş Yap
                        </Link>
                        <Link href="/register" className="btn-primary">
                            Ücretsiz Dene
                        </Link>
                    </div>
                </nav>

                {/* Hero Section */}
                <div className="text-center max-w-4xl mx-auto">
                    <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
                        Trendyol Satışlarınızın
                        <span className="text-primary-400"> Gerçek Kârını</span> Görün
                    </h1>
                    <p className="text-xl text-slate-300 mb-8">
                        Komisyon, KDV, kargo ve tüm maliyetleri hesaba katarak her ürününüzün
                        <br />
                        net kârlılığını analiz edin. Pazarsis ve Melontik alternatifi.
                    </p>
                    <div className="flex gap-4 justify-center">
                        <Link href="/register" className="btn-primary text-lg px-8 py-3">
                            Hemen Başla
                        </Link>
                        <Link href="#features" className="btn-secondary text-lg px-8 py-3">
                            Özellikler
                        </Link>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid md:grid-cols-3 gap-8 mt-20 max-w-4xl mx-auto">
                    <div className="text-center">
                        <div className="text-4xl font-bold text-primary-400">%100</div>
                        <div className="text-slate-400 mt-2">Doğru KDV Hesaplama</div>
                    </div>
                    <div className="text-center">
                        <div className="text-4xl font-bold text-primary-400">Anlık</div>
                        <div className="text-slate-400 mt-2">Senkronizasyon</div>
                    </div>
                    <div className="text-center">
                        <div className="text-4xl font-bold text-primary-400">Excel</div>
                        <div className="text-slate-400 mt-2">Uyumlu Raporlar</div>
                    </div>
                </div>

                {/* Features */}
                <div id="features" className="mt-32">
                    <h2 className="text-3xl font-bold text-white text-center mb-12">
                        Neler Yapabilirsiniz?
                    </h2>
                    <div className="grid md:grid-cols-3 gap-8">
                        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                            <div className="w-12 h-12 bg-primary-500/20 rounded-lg flex items-center justify-center mb-4">
                                <span className="text-2xl">📊</span>
                            </div>
                            <h3 className="text-xl font-semibold text-white mb-2">Detaylı Kâr Analizi</h3>
                            <p className="text-slate-400">
                                Her sipariş kalemi için komisyon, KDV, kargo ve platform ücretlerini
                                ayrı ayrı görün.
                            </p>
                        </div>
                        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                            <div className="w-12 h-12 bg-primary-500/20 rounded-lg flex items-center justify-center mb-4">
                                <span className="text-2xl">📈</span>
                            </div>
                            <h3 className="text-xl font-semibold text-white mb-2">Görsel Dashboard</h3>
                            <p className="text-slate-400">
                                Günlük, haftalık ve aylık kâr grafiklerinizi takip edin.
                                En kârlı ve zararlı ürünlerinizi görün.
                            </p>
                        </div>
                        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700">
                            <div className="w-12 h-12 bg-primary-500/20 rounded-lg flex items-center justify-center mb-4">
                                <span className="text-2xl">📁</span>
                            </div>
                            <h3 className="text-xl font-semibold text-white mb-2">Excel Entegrasyonu</h3>
                            <p className="text-slate-400">
                                Ürün maliyetlerinizi toplu olarak Excel ile yükleyin.
                                Raporlarınızı Excel olarak indirin.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <footer className="mt-32 text-center text-slate-400 text-sm">
                    © 2024 Trendyol Kârlılık Analizi. Tüm hakları saklıdır.
                </footer>
            </div>
        </div>
    );
}
