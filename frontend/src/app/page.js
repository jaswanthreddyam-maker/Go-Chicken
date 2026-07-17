"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { ArrowRight, ChevronRight, Menu, X } from "lucide-react";

// ── Intersection Observer hook for scroll-triggered animations ───────
function useRevealOnScroll(options = {}) {
  const ref = useRef(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.unobserve(el);
        }
      },
      { threshold: 0.15, ...options }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return [ref, isVisible];
}

import dynamic from 'next/dynamic';

const IsometricWireframe = dynamic(() => import('@/components/landing/IsometricWireframe'), {
  ssr: false, // Optional: might help if it's purely visual and heavy
});

// ── Navbar ────────────────────────────────────────────────────────────
const Navbar = ({ isLoggedIn, onGetStarted }) => {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#FAFAFA]/95 backdrop-blur-sm border-b border-[#EBEBEB]">
      <div className="max-w-[1280px] mx-auto px-6 lg:px-10">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="p-1 border border-[#EBEBEB] group-hover:border-[#111111] transition-colors">
              <div className="w-5 h-5 relative">
                <Image
                  src="/logo.png"
                  alt="Go Chicken"
                  fill
                  className="object-contain"
                  priority
                />
              </div>
            </div>
            <span className="text-sm font-extrabold tracking-tight uppercase text-[#111111]">
              Go Chicken
            </span>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center gap-8">
            <a href="#platform" className="text-xs font-bold uppercase tracking-wider text-[#666666] hover:text-[#111111] transition-colors">
              Platform
            </a>
            <a href="#solutions" className="text-xs font-bold uppercase tracking-wider text-[#666666] hover:text-[#111111] transition-colors">
              Solutions
            </a>
            <a href="#pricing" className="text-xs font-bold uppercase tracking-wider text-[#666666] hover:text-[#111111] transition-colors">
              Pricing
            </a>
            <a href="/docs" className="text-xs font-bold uppercase tracking-wider text-[#666666] hover:text-[#111111] transition-colors">
              Docs
            </a>
          </div>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center gap-4">
            {isLoggedIn ? (
              <button
                onClick={(e) => onGetStarted(e, "/")}
                className="px-5 py-2.5 bg-[#111111] text-white text-xs font-bold uppercase tracking-wider hover:bg-black transition-colors"
              >
                Get Started
              </button>
            ) : (
              <>
                <button
                  onClick={(e) => onGetStarted(e, "/login")}
                  className="text-xs font-bold uppercase tracking-wider text-[#666666] hover:text-[#111111] transition-colors"
                >
                  Log in
                </button>
                <button
                  onClick={(e) => onGetStarted(e, "/signup")}
                  className="px-5 py-2.5 bg-[#111111] text-white text-xs font-bold uppercase tracking-wider hover:bg-black transition-colors"
                >
                  Sign Up
                </button>
              </>
            )}
          </div>

          {/* Mobile Menu Toggle */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 text-[#111111]"
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile Dropdown */}
      {mobileOpen && (
        <div className="md:hidden bg-[#FAFAFA] border-t border-[#EBEBEB]">
          <div className="px-6 py-4 space-y-3">
            <a href="#platform" className="block text-xs font-bold uppercase tracking-wider text-[#666666] py-2">Platform</a>
            <a href="#solutions" className="block text-xs font-bold uppercase tracking-wider text-[#666666] py-2">Solutions</a>
            <a href="#pricing" className="block text-xs font-bold uppercase tracking-wider text-[#666666] py-2">Pricing</a>
            <a href="/docs" className="block text-xs font-bold uppercase tracking-wider text-[#666666] py-2">Docs</a>
            <div className="border-t border-[#EBEBEB] pt-3 space-y-2">
              {isLoggedIn ? (
                <button
                  onClick={(e) => { setMobileOpen(false); onGetStarted(e, "/"); }}
                  className="block w-full text-center px-5 py-3 bg-[#111111] text-white text-xs font-bold uppercase tracking-wider"
                >
                  Get Started
                </button>
              ) : (
                <>
                  <button
                    onClick={(e) => { setMobileOpen(false); onGetStarted(e, "/login"); }}
                    className="block w-full text-left text-xs font-bold uppercase tracking-wider text-[#666666] py-2"
                  >
                    Log in
                  </button>
                  <button
                    onClick={(e) => { setMobileOpen(false); onGetStarted(e, "/signup"); }}
                    className="block w-full text-center px-5 py-3 bg-[#111111] text-white text-xs font-bold uppercase tracking-wider"
                  >
                    Sign Up
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

// ── Logos Marquee (Social Proof) ──────────────────────────────────────
const LogoBar = () => {
  const logos = [
    "Suguna Foods",
    "Venky's India",
    "SKM Egg Products",
    "Godrej Agrovet",
    "IB Group",
    "Amrit Feeds",
  ];

  const doubled = [...logos, ...logos];

  return (
    <div className="border-t border-b border-[#EBEBEB] py-6 mt-0 overflow-hidden">
      <div className="max-w-[1280px] mx-auto px-6 lg:px-10">
        <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#999999] mb-5 text-center">
          Trusted by leading poultry enterprises across India
        </p>
      </div>
      <div className="relative">
        <div className="flex items-center gap-16 animate-marquee">
          {doubled.map((name, i) => (
            <div
              key={`${name}-${i}`}
              className="text-[11px] font-extrabold uppercase tracking-wider text-[#C0C0C0] whitespace-nowrap select-none shrink-0"
            >
              {name}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ── Feature Row (Below the Fold) ─────────────────────────────────────
const FeatureRow = () => {
  const features = [
    {
      title: "WhatsApp Order Engine",
      desc: "Retailers place orders via WhatsApp. Our NLP engine parses Telugu and English voice notes into structured line items — zero manual data entry.",
      tag: "AI · NLP",
    },
    {
      title: "IoT Fleet Intelligence",
      desc: "Real-time cold-chain monitoring across your entire fleet. Temperature, GPS, and load capacity — streamed to your dashboard every 15 seconds.",
      tag: "IoT · MQTT",
    },
    {
      title: "Retailer Khata Ledger",
      desc: "Digital credit ledger with automated settlement reminders. Every transaction is audit-ready, exportable, and legally compliant.",
      tag: "FinOps",
    },
  ];

  const [sectionRef, sectionVisible] = useRevealOnScroll();

  return (
    <section id="platform" className="py-20 lg:py-28" ref={sectionRef}>
      <div className="max-w-[1280px] mx-auto px-6 lg:px-10">
        <div
          className={`mb-14 transition-all duration-700 ${
            sectionVisible
              ? "opacity-100 translate-y-0"
              : "opacity-0 translate-y-6"
          }`}
        >
          <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#999999] mb-3">
            The Platform
          </p>
          <h2 className="text-2xl md:text-3xl font-black tracking-tight text-[#111111] max-w-lg leading-tight">
            Every tool your poultry hub needs. Nothing it doesn&apos;t.
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-0 border border-[#EBEBEB] divide-y md:divide-y-0 md:divide-x divide-[#EBEBEB]">
          {features.map((f, idx) => (
            <div
              key={f.title}
              className={`p-8 group hover:bg-white transition-all duration-500 ${
                sectionVisible
                  ? "opacity-100 translate-y-0"
                  : "opacity-0 translate-y-8"
              }`}
              style={{
                transitionDelay: sectionVisible ? `${200 + idx * 120}ms` : "0ms",
              }}
            >
              <span className="text-[9px] font-bold uppercase tracking-[0.15em] text-[#999999] border border-[#EBEBEB] px-2 py-1 inline-block mb-5">
                {f.tag}
              </span>
              <h3 className="text-base font-extrabold text-[#111111] tracking-tight mb-3">
                {f.title}
              </h3>
              <p className="text-sm text-[#666666] leading-relaxed font-medium">
                {f.desc}
              </p>
              <a
                href="#"
                className="inline-flex items-center gap-1.5 mt-6 text-xs font-bold uppercase tracking-wider text-[#111111] group-hover:gap-3 transition-all"
              >
                Learn more <ChevronRight size={14} />
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// ── Bottom CTA with scroll-reveal ────────────────────────────────────
const BottomCTA = ({ isLoggedIn, onGetStarted }) => {
  const [ref, isVisible] = useRevealOnScroll();
  return (
    <section ref={ref} className="border-t border-[#EBEBEB] py-16 lg:py-20">
      <div
        className={`max-w-[1280px] mx-auto px-6 lg:px-10 text-center transition-all duration-700 ${
          isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
        }`}
      >
        <h2 className="text-xl md:text-2xl font-black tracking-tight text-[#111111] mb-4">
          Ready to modernize your poultry supply chain?
        </h2>
        <p className="text-sm text-[#666666] font-medium mb-8 max-w-md mx-auto">
          Join hundreds of distributors who eliminated manual order
          tracking and reduced cold-chain losses by 40%.
        </p>
        <button
          onClick={(e) => onGetStarted(e, "/signup")}
          className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-[#111111] text-white text-xs font-bold uppercase tracking-wider hover:bg-black hover:scale-[1.03] active:scale-[0.98] transition-all w-full sm:w-auto"
        >
          {isLoggedIn ? "Get Started" : "Get started — it's free"}
          <ArrowRight size={14} />
        </button>
      </div>
    </section>
  );
};

// ── Page Component ───────────────────────────────────────────────────
export default function LandingPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => {
      setMounted(true);
      if (typeof window !== "undefined") {
        if (window.location.hash.includes("access_token")) {
          router.push("/auth/callback" + window.location.hash);
          return;
        }
        sessionStorage.setItem("gc_visited_landing", "true");
        const userStr = localStorage.getItem("gc_user");
        if (userStr) {
          setIsLoggedIn(true);
        }
      }
    }, 0);
    return () => clearTimeout(t);
  }, [router]);

  const handleGetStarted = (e, fallbackRoute = "/signup") => {
    e.preventDefault();
    if (isLoggedIn) {
      sessionStorage.removeItem("gc_welcome_played");
      router.push("/dashboard");
    } else {
      router.push(fallbackRoute);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAFAFA] text-[#111111] font-sans">
      <Navbar isLoggedIn={isLoggedIn} onGetStarted={handleGetStarted} />

      {/* ── Hero Section ─────────────────────────────────────── */}
      <section className="pt-16">
        {/* pt-16 accounts for the fixed navbar height */}
        <div className="max-w-[1280px] mx-auto px-6 lg:px-10">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-0 min-h-[calc(100vh-64px)] items-center">
            {/* ── Left: Copy ──────────────────────────────────── */}
            <div className="py-16 lg:py-0 lg:pr-16">
              <p
                className={`text-[10px] font-bold uppercase tracking-[0.2em] text-[#999999] mb-5 transition-all duration-700 ${
                  mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
                }`}
                style={{ transitionDelay: mounted ? "100ms" : "0ms" }}
              >
                B2B Poultry Supply Chain SaaS
              </p>

              <h1
                className={`text-[clamp(2.2rem,5.5vw,4.2rem)] font-black leading-[0.95] tracking-[-0.03em] text-[#111111] mb-6 transition-all duration-700 ${
                  mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"
                }`}
                style={{ fontStretch: "condensed", transitionDelay: mounted ? "250ms" : "0ms" }}
              >
                Push Your
                <br />
                Poultry Hub
                <br />
                <span className="text-[#666666]">to the Web.</span>
              </h1>

              <p
                className={`text-sm md:text-base text-[#666666] leading-relaxed font-medium max-w-md mb-10 transition-all duration-700 ${
                  mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
                }`}
                style={{ transitionDelay: mounted ? "450ms" : "0ms" }}
              >
                Go Chicken unifies WhatsApp orders, IoT fleet monitoring,
                retailer credit ledgers, and AI demand forecasting into a
                single enterprise-grade platform — built for India&apos;s
                poultry distributors.
              </p>

              {/* CTA Row */}
              <div
                className={`flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full sm:w-auto transition-all duration-700 ${
                  mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
                }`}
                style={{ transitionDelay: mounted ? "600ms" : "0ms" }}
              >
                <button
                  onClick={(e) => handleGetStarted(e, "/signup")}
                  className="group flex items-center justify-center gap-2 px-7 py-3.5 bg-[#111111] text-white text-xs font-bold uppercase tracking-wider hover:bg-black hover:scale-[1.03] active:scale-[0.98] transition-all w-full sm:w-auto"
                >
                  {isLoggedIn ? "Get Started" : "Start for free"}
                  <ArrowRight
                    size={14}
                    className="group-hover:translate-x-1 transition-transform"
                  />
                </button>
                <a
                  href="#"
                  className="flex items-center justify-center px-7 py-3.5 border border-[#111111] text-[#111111] text-xs font-bold uppercase tracking-wider hover:bg-[#111111] hover:text-white hover:scale-[1.03] active:scale-[0.98] transition-all w-full sm:w-auto"
                >
                  Talk to sales
                </a>
              </div>

              {/* Micro proof */}
              <p
                className={`mt-8 text-[10px] font-bold uppercase tracking-[0.15em] text-[#AEAEAE] transition-all duration-700 ${
                  mounted ? "opacity-100" : "opacity-0"
                }`}
                style={{ transitionDelay: mounted ? "800ms" : "0ms" }}
              >
                No credit card required · Setup in under 2 minutes
              </p>
            </div>

            {/* ── Right: Hero Graphic ────────────────────────── */}
            <div className="hidden lg:flex items-center justify-center border-l border-[#EBEBEB] pl-10 relative">
              <Image
                src="/hero-graphic.png"
                alt="Go Chicken platform — logistics and data dashboard"
                width={540}
                height={540}
                className="w-full h-auto max-w-[540px] object-contain rounded-2xl animate-float mix-blend-multiply"
                priority
              />
            </div>

            {/* Mobile: Show graphic below copy */}
            <div className="lg:hidden flex items-center justify-center py-8 relative">
              <div className="w-full max-w-md relative">
                <Image
                  src="/hero-graphic.png"
                  alt="Go Chicken platform — logistics and data dashboard"
                  width={540}
                  height={540}
                  className="w-full h-auto object-contain rounded-2xl mix-blend-multiply"
                  priority
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Logo Bar ─────────────────────────────────────────── */}
      <LogoBar />

      {/* ── Features Section ─────────────────────────────────── */}
      <FeatureRow />

      {/* ── Bottom CTA Band ──────────────────────────────────── */}
      <BottomCTA isLoggedIn={isLoggedIn} onGetStarted={handleGetStarted} />

      {/* ── Footer ───────────────────────────────────────────── */}
      <footer className="border-t border-[#EBEBEB] py-10">
        <div className="max-w-[1280px] mx-auto px-6 lg:px-10 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="p-1 border border-[#EBEBEB]">
              <img
                src="/logo.png"
                alt="Go Chicken"
                className="w-4 h-4 object-contain"
              />
            </div>
            <span className="text-xs font-extrabold uppercase tracking-tight text-[#111111]">
              Go Chicken
            </span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#" className="text-[10px] font-bold uppercase tracking-wider text-[#999999] hover:text-[#111111] transition-colors">
              Privacy
            </a>
            <a href="#" className="text-[10px] font-bold uppercase tracking-wider text-[#999999] hover:text-[#111111] transition-colors">
              Terms
            </a>
            <a href="#" className="text-[10px] font-bold uppercase tracking-wider text-[#999999] hover:text-[#111111] transition-colors">
              Status
            </a>
          </div>
          <p className="text-[10px] font-bold uppercase tracking-wider text-[#AEAEAE]">
            © 2026 Go Chicken. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
