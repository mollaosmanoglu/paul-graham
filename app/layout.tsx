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

export const metadata: Metadata = {
  title: {
    default: "Paul Graham's Wisdom",
    template: "%s — Paul Graham's Wisdom",
  },
  description: '231 essays. 17 chapters. In his own words.',
  robots: { index: false, follow: false },
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
