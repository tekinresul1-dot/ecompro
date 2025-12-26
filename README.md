# Trendyol Kârlılık Analizi SaaS

Trendyol satıcıları için profesyonel kâr analizi ve raporlama platformu.

## 🎯 Proje Amacı

Bu uygulama, Trendyol satıcılarının sipariş başına gerçek kârlılığını hesaplayarak:
- Komisyon, KDV, kargo ve platform ücretlerini ayrıştırır
- Her ürün için net kâr marjını gösterir
- Zararlı ürünleri tespit eder
- Günlük/aylık kâr trendlerini görselleştirir

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │Dashboard│  │Products │  │ Orders  │  │  Calculations   │ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼────────────────────────────────┐
│                    Backend (Django + DRF)                    │
│  ┌──────────┐  ┌────────┐  ┌────────┐  ┌─────────────────┐  │
│  │ Accounts │  │Sellers │  │Products│  │   Calculations  │  │
│  └──────────┘  └────────┘  └────────┘  └─────────────────┘  │
│  ┌──────────┐  ┌────────┐  ┌────────────────────────────┐   │
│  │  Orders  │  │Analytics│ │  Trendyol Integration      │   │
│  └──────────┘  └────────┘  └────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   ┌────────┐          ┌──────────┐         ┌─────────┐
   │PostgreSQL│        │  Redis   │         │Trendyol │
   │ (Veritabanı)│     │ (Cache)  │         │   API   │
   └────────┘          └──────────┘         └─────────┘
```

## 📁 Proje Yapısı

```
genel/
├── backend/                  # Django Backend
│   ├── apps/
│   │   ├── accounts/         # Kullanıcı yönetimi
│   │   ├── sellers/          # Satıcı hesapları
│   │   ├── products/         # Ürün yönetimi
│   │   ├── orders/           # Sipariş yönetimi
│   │   ├── calculations/     # Kâr hesaplamaları
│   │   ├── analytics/        # Dashboard & Raporlar
│   │   └── integrations/     # Trendyol API entegrasyonu
│   ├── config/               # Django ayarları
│   ├── core/                 # Ortak yardımcılar
│   ├── requirements.txt
│   └── manage.py
│
└── frontend/                 # Next.js Frontend
    ├── src/
    │   ├── app/              # Sayfalar
    │   ├── components/       # React bileşenleri
    │   └── lib/              # API, auth, utils
    ├── package.json
    └── tailwind.config.js
```

## 🚀 Kurulum

### Backend

```bash
cd backend

# Virtual environment oluştur
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate    # Windows

# Bağımlılıkları yükle
pip install -r requirements.txt

# Environment dosyasını oluştur
cp .env.example .env
# .env dosyasını düzenle

# Veritabanı migrasyonları
python manage.py migrate

# Süper kullanıcı oluştur
python manage.py createsuperuser

# Geliştirme sunucusunu başlat
python manage.py runserver
```

### Frontend

```bash
cd frontend

# Bağımlılıkları yükle
npm install

# Environment dosyasını oluştur
cp .env.local.example .env.local

# Geliştirme sunucusunu başlat
npm run dev
```

## ⚙️ Environment Değişkenleri

### Backend (.env)

```env
DEBUG=True
SECRET_KEY=your-secret-key

# Database
DB_NAME=trendyol_profit
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Encryption (Fernet key - 32 bytes base64 encoded)
ENCRYPTION_KEY=your-fernet-key
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 📊 Kâr Hesaplama Formülü

```
1. Net Satış = Birim Fiyat × Adet - İndirim
2. Satış KDV = Net Satış - (Net Satış / (1 + KDV Oranı))
3. Net Satış (KDV Hariç) = Net Satış - Satış KDV
4. Komisyon = Net Satış (KDV Hariç) × Komisyon Oranı
5. Komisyon KDV = Komisyon × Komisyon KDV Oranı
6. Toplam İndirilecek KDV = Alış KDV + Komisyon KDV + Kargo KDV + Platform KDV
7. Ödenecek KDV = Satış KDV - Toplam İndirilecek KDV
8. Toplam Maliyet = Ürün Maliyeti + Ödenecek KDV + Komisyon + Kargo + Platform
9. Net Kâr = Net Satış (KDV Hariç) - Toplam Maliyet
10. Kâr Marjı = (Net Kâr / Net Satış KDV Hariç) × 100
```

## 🔑 API Endpoints

### Authentication
- `POST /api/v1/auth/register/` - Kayıt
- `POST /api/v1/auth/login/` - Giriş
- `POST /api/v1/auth/logout/` - Çıkış
- `GET /api/v1/auth/profile/` - Profil

### Sellers
- `GET /api/v1/sellers/` - Liste
- `POST /api/v1/sellers/` - Yeni ekle
- `POST /api/v1/sellers/{id}/sync/` - Senkronize et

### Products
- `GET /api/v1/products/` - Liste
- `PATCH /api/v1/products/{id}/cost/` - Maliyet güncelle
- `POST /api/v1/products/bulk-upload/` - Toplu yükle
- `GET /api/v1/products/export/` - Excel indir

### Orders
- `GET /api/v1/orders/` - Liste
- `GET /api/v1/orders/{id}/` - Detay
- `GET /api/v1/orders/summary/` - Özet

### Calculations
- `GET /api/v1/calculations/{id}/breakdown/` - Hesaplama detayı
- `POST /api/v1/calculations/trigger/order/{id}/` - Hesapla
- `GET /api/v1/calculations/daily/` - Günlük özetler
- `GET /api/v1/calculations/products/top/` - Top ürünler
- `GET /api/v1/calculations/products/loss/` - Zararlı ürünler

### Analytics
- `GET /api/v1/analytics/dashboard/` - Dashboard verileri
- `GET /api/v1/analytics/daily/` - Günlük grafik
- `GET /api/v1/analytics/cost-breakdown/` - Maliyet dağılımı

## 🛠️ Teknolojiler

### Backend
- Python 3.11+
- Django 5.0
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- JWT Authentication

### Frontend
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- React Query
- Recharts

## 📝 Celery Görevleri

```bash
# Worker başlat
celery -A config worker -l info

# Beat (zamanlayıcı) başlat
celery -A config beat -l info
```

## 🔒 Güvenlik

- API anahtarları Fernet ile şifrelenir
- JWT token ile kimlik doğrulama
- CORS yapılandırması
- Rate limiting (Trendyol API)

## 📄 Lisans

MIT License

## 👥 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın
