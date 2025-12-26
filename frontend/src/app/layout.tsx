import type { Metadata } from 'next';
import './globals.css';
import { Providers } from './providers';

export const metadata: Metadata = {
    title: 'Trendyol Kârlılık Analizi',
    description: 'Trendyol satıcıları için profesyonel kâr analizi ve raporlama platformu',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="tr">
            <body>
                <Providers>{children}</Providers>
            </body>
        </html>
    );
}
