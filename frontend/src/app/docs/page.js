"use client";

import React from 'react';
import { ChevronLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Head from 'next/head';

export default function DocsPage() {
  const router = useRouter();

  return (
    <div className="h-screen w-screen flex flex-col bg-[#FAFAFA] overflow-hidden">
      <Head>
        <title>Docs - Go Chicken</title>
      </Head>

      {/* Header */}
      <header className="flex-none bg-white border-b border-[#EBEBEB] px-4 py-3 flex items-center gap-3 shadow-sm z-10">
        <button 
          onClick={() => router.back()}
          className="p-1.5 -ml-1.5 hover:bg-[#FAFAFA] rounded-md transition-colors"
          aria-label="Go back"
        >
          <ChevronLeft size={24} className="text-[#111111]" />
        </button>
        <h1 className="text-sm font-extrabold tracking-tight uppercase flex-1">Documentation & Pitch Deck</h1>
      </header>

      {/* PDF Viewer Container */}
      <main className="flex-1 w-full h-full relative">
        <iframe 
          src="/Go-Chicken-Pitch-Deck.pdf#view=FitH" 
          className="absolute inset-0 w-full h-full border-none"
          title="Go Chicken Pitch Deck"
          allowFullScreen
        >
          <p>Your browser does not support PDFs. <a href="/Go-Chicken-Pitch-Deck.pdf">Download the PDF</a>.</p>
        </iframe>
      </main>
    </div>
  );
}
