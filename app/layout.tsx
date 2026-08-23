import { RootProvider } from 'fumadocs-ui/provider/next';
import './global.css';
import { Outfit } from 'next/font/google';
import type { Metadata, Viewport } from 'next';
import { BookChat } from '@/components/book-chat';

const outfit = Outfit({
  subsets: ['latin'],
  weight: ['300', '400', '500'],
});

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
};

const siteUrl = process.env.VERCEL_PROJECT_PRODUCTION_URL
  ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
  : process.env.VERCEL_URL
    ? `https://${process.env.VERCEL_URL}`
    : 'http://localhost:3000';

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "Paul Graham's Wisdom",
    template: "%s — Paul Graham's Wisdom",
  },
  description: '231 essays. 547 lessons. In his own words.',
  openGraph: {
    title: "Paul Graham's Wisdom",
    description: '231 essays. 547 lessons. In his own words.',
    type: 'website',
    siteName: "Paul Graham's Wisdom",
    images: [
      {
        url: '/og.png',
        width: 1200,
        height: 630,
        alt: "Paul Graham's Wisdom — 231 essays. 547 lessons.",
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: "Paul Graham's Wisdom",
    description: '231 essays. 547 lessons. In his own words.',
    images: ['/og.png'],
  },
  robots: { index: false, follow: true },
};

export default function Layout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="en" className={outfit.className} suppressHydrationWarning>
      <body className="flex flex-col min-h-screen font-light">
        <RootProvider theme={{ defaultTheme: 'light' }}>
          {children}
          <BookChat />
        </RootProvider>
      </body>
    </html>
  );
}
