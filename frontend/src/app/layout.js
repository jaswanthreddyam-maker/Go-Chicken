import { Geist, Geist_Mono, Inter } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "@/context/LanguageContext";
import { UIProvider } from "@/context/UIContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata = {
  title: "Go Chicken — Enterprise Poultry SaaS",
  description: "Enterprise-grade poultry supply chain management dashboard with IoT fleet tracking, AI demand forecasting, and WhatsApp order automation.",
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${inter.variable} h-full antialiased light`}
      style={{ colorScheme: 'light' }}
    >
      <head>
        <meta name="darkreader-lock" />
      </head>
      <body className="min-h-full flex flex-col bg-white text-[#111111]">
        <UIProvider>
          <LanguageProvider>
            {children}
          </LanguageProvider>
        </UIProvider>
      </body>
    </html>
  );
}
