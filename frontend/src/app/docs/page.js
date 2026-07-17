"use client";
import React, { useState, useEffect } from 'react';
import { ChevronLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Head from 'next/head';

// Import Sections
import Hero from '@/components/docs/Hero';
import Problem from '@/components/docs/Problem';
import StoryTimeline from '@/components/docs/StoryTimeline';
import WhyWhatsapp from '@/components/docs/WhyWhatsapp';
import LiveDemo from '@/components/docs/LiveDemo';
import Architecture from '@/components/docs/Architecture';
import Enterprise from '@/components/docs/Enterprise';
import BusinessImpact from '@/components/docs/BusinessImpact';
import Roadmap from '@/components/docs/Roadmap';
import Closing from '@/components/docs/Closing';

export default function PresentationPage() {
  const router = useRouter();
  const [activeSection, setActiveSection] = useState('hero');

  const sections = [
    { id: 'hero', label: 'Hero' },
    { id: 'problem', label: 'Problem' },
    { id: 'raj', label: 'Raj' },
    { id: 'whatsapp', label: 'WhatsApp' },
    { id: 'demo', label: 'Demo' },
    { id: 'architecture', label: 'Architecture' },
    { id: 'engineering', label: 'Engineering' },
    { id: 'impact', label: 'Impact' },
    { id: 'roadmap', label: 'Roadmap' },
    { id: 'closing', label: 'Closing' },
  ];

  // Intersection Observer for scroll spy
  useEffect(() => {
    const observerOptions = {
      root: null,
      rootMargin: '-40% 0px -40% 0px', // Trigger when section is around the middle of the screen
      threshold: 0
    };

    const observerCallback = (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          setActiveSection(entry.target.id);
        }
      });
    };

    const observer = new IntersectionObserver(observerCallback, observerOptions);

    sections.forEach((section) => {
      const element = document.getElementById(section.id);
      if (element) observer.observe(element);
    });

    return () => observer.disconnect();
  }, []);

  return (
    <div className="min-h-screen bg-white text-[#111111] font-sans selection:bg-[#111111] selection:text-white">
      <Head>
        <title>Go Chicken - The Presentation</title>
      </Head>

      {/* Subtle Header */}
      <header className="fixed top-0 left-0 right-0 z-50 px-4 py-4 flex items-center justify-between mix-blend-difference text-white pointer-events-none">
        <button 
          onClick={() => router.back()}
          className="p-2 hover:bg-white/10 rounded-full transition-colors pointer-events-auto backdrop-blur-sm"
          aria-label="Go back"
        >
          <ChevronLeft size={24} />
        </button>
        <span className="text-xs font-bold tracking-widest uppercase opacity-50 hidden sm:block">Internal Pitch Deck</span>
      </header>

      {/* Floating Progress Indicator */}
      <div className="fixed right-6 top-1/2 -translate-y-1/2 z-50 hidden lg:flex flex-col gap-3 pointer-events-none">
        {sections.map((section) => (
          <div key={section.id} className="flex items-center justify-end gap-3 group">
            <span className={`text-[10px] font-bold uppercase tracking-wider transition-opacity duration-300 ${activeSection === section.id ? 'opacity-100 text-[#111111]' : 'opacity-0 text-[#AEAEAE]'}`}>
              {section.label}
            </span>
            <div className={`w-2 h-2 rounded-full transition-all duration-300 ${activeSection === section.id ? 'bg-[#111111] scale-125' : 'border border-[#AEAEAE] bg-transparent'}`} />
          </div>
        ))}
      </div>

      {/* Presentation Content */}
      <main>
        <Hero />
        <Problem />
        <StoryTimeline />
        <WhyWhatsapp />
        <LiveDemo />
        <Architecture />
        <Enterprise />
        <BusinessImpact />
        <Roadmap />
        <Closing />
      </main>
    </div>
  );
}
